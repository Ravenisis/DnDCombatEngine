from pathlib import Path
from types import SimpleNamespace

import pytest

from dnd_combat_engine.controllers import CharacterImportController
from dnd_combat_engine.models import Campaign, DamageType, HitPoints, RuleSource
from dnd_combat_engine.models.imports import CharacterImportDraft
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import (
    CampaignService,
    CharacterImportError,
    CharacterImportService,
    PersistenceService,
)
from dnd_combat_engine.services.character_import_service import _extract_pdf_literal_text

FIXTURES = Path(__file__).parent / "fixtures" / "imports"

SHEET_TEXT = """
Character Name: Lyra Thorn
Class & Level: Rogue 3
Armor Class: 15
Current HP: 19
Max HP: 24
Temporary HP: 4
STR 8
DEX 16
CON 14
INT 12
WIS 10
CHA 13
Skills: Acrobatics, Stealth, Perception
Equipment: thieves' tools, rope, torch
Weapons:
Rapier +5 1d8 piercing
Shortbow +5 1d6 piercing
"""


def test_character_import_service_parses_text_sheet() -> None:
    draft = CharacterImportService().parse_text(SHEET_TEXT, source="test")

    assert draft.name == "Lyra Thorn"
    assert draft.level == 3
    assert draft.hit_points.current == 19
    assert draft.hit_points.maximum == 24
    assert draft.hit_points.temporary == 4
    assert draft.abilities.dexterity == 16
    assert draft.skills == ("Acrobatics", "Stealth", "Perception")
    assert [item.name for item in draft.inventory] == ["thieves' tools", "rope", "torch"]
    assert [weapon.name for weapon in draft.weapons] == ["Rapier", "Shortbow"]
    assert draft.armor is not None
    assert draft.armor.armor_class == 15


def test_character_import_service_ignores_attack_table_fragments() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Actions
        Handaxe +4 1d6 slashing
        Warhammer +4 1d8 bludgeoning
        instead 1d6 slashing
        Range 1d6 slashing
        Unarmed Strike +4 2 bludgeoning
        """,
        source="test",
    )

    assert [weapon.name for weapon in draft.weapons] == ["Handaxe", "Warhammer"]


def test_character_import_draft_can_keep_rule_source_metadata() -> None:
    source = RuleSource.srd_5_2_1("character-creation.md")
    draft = CharacterImportDraft("Lyra Thorn", rule_source=source)

    assert draft.rule_source == source
    assert draft.to_character("lyra").name == "Lyra Thorn"


def test_character_import_service_ignores_noisy_dnd_beyond_skill_footer() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Skills: SAVESHIT DICE, Total SUCCESSES, FAILURES, HIT POINTS,
        Max HP Current HP Temp HP, SPEED, ARMOR, CLASS,
        TM & (c) 2018 Wizards of the Coast LLC. (c)2018 D&D Beyond | All Rights Reserved.
        PROFICIENCY BONUS,
        Inventory: Rope
        """,
        source="test",
    )

    assert draft.skills == ()


def test_character_import_service_reads_currency_from_sheet_text() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Inventory
        Bag of Holding
        2,989GP
        PP GP SP CP
        """,
        source="test",
    )

    assert draft.currency.pp == 298
    assert draft.currency.gp == 9
    assert draft.currency.sp == 0
    assert draft.currency.cp == 0


def test_character_import_service_reads_dnd_beyond_label_below_name() -> None:
    draft = CharacterImportService().parse_text(
        """
        Ravenisis
        CHARACTER NAME
        Cleric 6
        CLASS & LEVEL
        wazic
        PLAYER NAME
        Hill Dwarf
        SPECIES
        Folk Hero
        BACKGROUND
        """,
        source="test",
    )

    assert draft.name == "Ravenisis"


def test_character_import_service_preserves_display_case_for_imported_name(tmp_path) -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: fluxor
        Fluxor
        CHARACTER NAME
        Class & Level: Fighter 4
        """,
        source="test",
    )
    persistence = PersistenceService(JsonFileStore(tmp_path))
    persistence.save_campaign(Campaign("starter", "Starter"))
    controller = CharacterImportController(
        CharacterImportService(),
        CampaignService(),
        persistence,
    )

    result = controller.import_draft_to_campaign(draft, "starter")

    assert draft.name == "Fluxor"
    assert result.character.character_id == "fluxor"
    assert persistence.load_character("fluxor").name == "Fluxor"


def test_character_import_service_adds_spell_slots_for_cleric_sheet() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Class & Level: Cleric 6
        Domain Spells: Bless, Cure Wounds, Revivify
        """,
        source="test",
    )
    character = draft.to_character("ravenisis")

    assert draft.resources["spell_slot_1"].maximum == 4
    assert draft.resources["spell_slot_2"].maximum == 3
    assert draft.resources["spell_slot_3"].maximum == 3
    assert character.resources["spell_slot_1"].current == 4
    assert character.resources["hit_dice"].maximum == 6


def test_character_import_adds_channel_uses_detect_magic_and_versatile_damage() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Class & Level: Cleric 6
        Channel Divinity: Turn Undead
        Warhammer +4 1d8+1 bludgeoning
        === 1st LEVEL ===
        Detect Magic
        Guiding Bolt
        """,
        source="test",
    )

    warhammer = draft.weapons[0]
    assert draft.resources["channel_divinity"].maximum == 2
    assert "Channel Divinity: Turn Undead" in draft.features
    assert "Detect Magic" in draft.spells
    assert warhammer.versatile_damage is not None
    assert warhammer.versatile_damage.components[0].dice == "1d10+1"


def test_character_import_preserves_other_named_channel_divinity_options() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Devotion
        Class & Level: Paladin 3
        Channel Divinity: Sacred Weapon
        Channel Divinity: Turn the Unholy
        """,
        source="test",
    )

    assert "Channel Divinity: Sacred Weapon" in draft.features
    assert "Channel Divinity: Turn the Unholy" in draft.features
    assert "Channel Divinity: Turn Undead" not in draft.features
    assert draft.resources["channel_divinity"].maximum == 1


def test_character_import_service_infers_core_cleric_armor_proficiencies() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Class & Level: Cleric 6
        ARMOR
        Heavy
        Armor,
        Plate,
        Shields
        WEAPONS
        Battleaxe,
        Simple
        Weapons,
        """,
        source="test",
    )

    assert draft.armor_proficiencies == (
        "Heavy Armor",
        "Light Armor",
        "Medium Armor",
        "Plate",
        "Shields",
    )


def test_character_import_service_prefers_class_feature_section() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Class & Level: Cleric 6
        Species: Hill Dwarf
        Background: Folk Hero
        === CLERIC FEATURES ===
        Spellcasting
        Channel Divinity
        Blessed Healer
        === CANTRIPS ===
        Light
        Sacred Flame
        """,
        source="test",
    )

    assert draft.features == (
        "Spellcasting",
        "Channel Divinity",
        "Blessed Healer",
        "Channel Divinity: Turn Undead",
        "Channel Divinity: Preserve Life",
    )


def test_character_import_service_labels_dnd_beyond_literal_values() -> None:
    literal_pdf = b"".join(
        [
            b"/V(Ravenisis)",
            b"/V(Cleric 6)",
            b"/V(wazic)",
            b"/V(Hill Dwarf)",
            b"/V(Folk Hero)",
            b"/V((Milestone))",
            b"/V(12)/V(+1)/V(13)/V(+1)/V(18)/V(+4)",
            b"/V(10)/V(+0)/V(15)/V(+2)/V(9)/V(-1)",
            b"/V(Darkvision 60 ft.)/V(20)/V(+3)/V(25 ft.)/V(63)/V(--)/V(6d8)",
            b"/V(Bag of Holding)/V(1)/V(5 lb.)/V(Potion of Healing (Greater))/V(1)/V(0.5 lb.)",
            b"/V(2,989GP)",
        ]
    )

    text = _extract_pdf_literal_text(literal_pdf)
    draft = CharacterImportService().parse_text(text, source="literal")

    assert draft.name == "Ravenisis"
    assert draft.level == 6
    assert draft.abilities.constitution == 18
    assert draft.hit_points.maximum == 63
    assert draft.armor is not None
    assert draft.armor.armor_class == 20
    assert draft.senses == ("Darkvision 60 ft.",)
    assert draft.proficiency_bonus == 3
    assert draft.walking_speed == 25
    assert [item.name for item in draft.inventory] == [
        "Bag of Holding",
        "Potion of Healing (Greater)",
    ]
    assert [item.quantity for item in draft.inventory] == [1, 1]
    assert [item.weight for item in draft.inventory] == [5.0, 0.5]
    assert draft.currency.pp == 298
    assert draft.currency.gp == 9


def test_character_import_service_parses_standard_dndbeyond_fixture() -> None:
    text = (FIXTURES / "dndbeyond_standard_extract.txt").read_text(encoding="utf-8")

    draft = CharacterImportService().parse_text(text, source="fixture")
    items = {item.name: item for item in draft.inventory}
    character = draft.to_character("ravenisis")

    assert draft.name == "Ravenisis"
    assert draft.level == 6
    assert draft.character_class == "Cleric 6"
    assert draft.race == "Hill Dwarf"
    assert draft.senses == ()
    assert draft.initiative_modifier == 1
    assert draft.proficiency_bonus == 3
    assert draft.ability_save_dc == 13
    assert draft.walking_speed is None
    assert draft.spellcasting_ability == "Wisdom"
    assert draft.spell_save_dc == 13
    assert draft.spell_attack_bonus == 5
    assert draft.saving_throw_modifiers == {
        "strength": 1,
        "dexterity": 1,
        "constitution": 4,
        "intelligence": 0,
        "wisdom": 5,
        "charisma": 2,
    }
    assert items["Clothes, Common"].quantity == 1
    assert items["Clothes, Common"].weight == 3.0
    assert items["Healer's Kit"].quantity == 3
    assert items["Rations (1 day)"].quantity == 8
    assert items["Potion of Healing (Greater)"].weight == 0.5
    assert items["Potion of Healing (Greater)"].category.value == "consumable"
    assert "restore" in (items["Potion of Healing (Greater)"].notes or "").lower()
    assert items["Healer's Kit"].category.value == "adventuring_gear"
    assert items["Healer's Kit"].purchase_price_cp > 0
    assert draft.currency.pp == 298
    assert draft.currency.gp == 9
    assert draft.tool_proficiencies == ("Cook's Utensils", "Mason's Tools", "Vehicles (Land)")
    assert draft.damage_resistances == (DamageType.NECROTIC, DamageType.POISON)
    assert draft.features == ()
    assert "Guiding Bolt" in draft.spells
    assert "Light" not in draft.spells
    assert "Sacred Flame" not in draft.spells
    assert "Thaumaturgy" not in draft.spells
    assert character.tool_proficiencies == draft.tool_proficiencies
    assert character.damage_resistances == draft.damage_resistances


def test_character_import_service_parses_machine_readable_fixture() -> None:
    text = (FIXTURES / "machine_readable_extract.txt").read_text(encoding="utf-8")

    draft = CharacterImportService().parse_text(text, source="fixture")
    items = {item.name: item for item in draft.inventory}

    assert draft.name == "Ravenisis"
    assert draft.skills == ("Animal Handling", "Insight", "Medicine", "Survival")
    assert draft.saving_throw_proficiencies == ("Wisdom", "Charisma")
    assert draft.saving_throw_modifiers == {
        "strength": 1,
        "dexterity": 1,
        "constitution": 4,
        "intelligence": 0,
        "wisdom": 5,
        "charisma": 2,
    }
    assert draft.armor_proficiencies == (
        "Heavy Armor",
        "Light Armor",
        "Medium Armor",
        "Plate",
        "Shields",
    )
    assert draft.weapon_proficiencies == ("Battleaxe", "Simple Weapons", "Warhammer")
    assert draft.tool_proficiencies == ("Cook's Utensils", "Mason's Tools", "Vehicles (Land)")
    assert draft.languages == ("Common", "Dwarvish")
    assert draft.damage_resistances == (DamageType.NECROTIC, DamageType.POISON)
    assert draft.currency.pp == 298
    assert draft.currency.gp == 9
    assert draft.character_class == "Cleric 6"
    assert draft.race == "Hill Dwarf"
    assert draft.senses == ()
    assert draft.initiative_modifier == 0
    assert draft.proficiency_bonus == 3
    assert draft.ability_save_dc == 11
    assert draft.spellcasting_ability == "Wisdom"
    assert draft.spell_save_dc == 11
    assert draft.spell_attack_bonus == 3
    assert items["Clothes, Common"].quantity == 1
    assert items["Playing Card Set"].weight == 0.0
    assert items["Healer's Kit"].quantity == 3
    assert items["Potion of Healing (Greater)"].weight == 0.5
    assert "Channel Divinity" in draft.features
    assert "Channel Divinity: Turn Undead" in draft.features
    assert "Channel Divinity: Preserve Life" in draft.features
    assert "Blessed Healer" in draft.features
    assert "Guiding Bolt" in draft.spells
    assert "Lesser Restoration" in draft.spells
    assert "Beacon of Hope" in draft.spells
    assert "Light" not in draft.spells


def test_character_import_service_extracts_numbered_spells_but_skips_cantrips() -> None:
    draft = CharacterImportService().parse_text(
        """
        Character Name: Ravenisis
        Class & Level: Cleric 6
        === CANTRIPS ===
        Light
        Sacred Flame
        Thaumaturgy
        === 1st LEVEL ===
        Healing Word
        Guiding Bolt
        === 2nd LEVEL ===
        Aid
        Lesser Restoration
        === 3rd LEVEL ===
        Spirit Guardians
        Beacon of Hope
        """,
        source="test",
    )

    assert draft.spells == (
        "Guiding Bolt",
        "Healing Word",
        "Aid",
        "Lesser Restoration",
        "Beacon of Hope",
        "Spirit Guardians",
    )
    assert not {"Light", "Sacred Flame", "Thaumaturgy"}.intersection(draft.spells)


def test_character_import_service_parses_public_html_url(monkeypatch) -> None:
    service = CharacterImportService()

    monkeypatch.setattr(
        service,
        "_fetch_url",
        lambda url: SimpleNamespace(
            content=b"""
            <html><body>
            <h1>Character Name: Lyra Thorn</h1>
            <p>Level: 3</p>
            <p>Hit Points: 19</p>
            <p>DEX 16</p>
            </body></html>
            """,
            content_type="text/html; charset=utf-8",
            final_url=url,
        ),
    )

    draft = service.import_url("https://example.test/characters/lyra")

    assert draft.name == "Lyra Thorn"
    assert draft.level == 3
    assert draft.hit_points.maximum == 19
    assert draft.abilities.dexterity == 16


def test_character_import_service_follows_dndbeyond_character_page_pdf_link(
    monkeypatch,
) -> None:
    service = CharacterImportService()
    calls = []

    def fake_fetch(url: str):
        calls.append(url)
        if url == "https://www.dndbeyond.com/characters/92446074":
            return SimpleNamespace(
                content=(b'<html><a href="/sheet-pdfs/wazic_92446074.pdf">Export PDF</a></html>'),
                content_type="text/html; charset=utf-8",
                final_url=url,
            )
        if url == "https://www.dndbeyond.com/sheet-pdfs/wazic_92446074.pdf":
            return SimpleNamespace(
                content=b"%PDF test",
                content_type="application/pdf",
                final_url=url,
            )
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(service, "_fetch_url", fake_fetch)
    monkeypatch.setattr(
        service,
        "_extract_pdf_bytes",
        lambda content: (
            """
        Character Name: Ravenisis
        Class & Level: Cleric 6
        Current HP: 63
        """
        ),
    )

    draft = service.import_url("https://www.dndbeyond.com/characters/92446074")

    assert calls == [
        "https://www.dndbeyond.com/characters/92446074",
        "https://www.dndbeyond.com/sheet-pdfs/wazic_92446074.pdf",
    ]
    assert draft.name == "Ravenisis"
    assert draft.level == 6
    assert draft.source == "https://www.dndbeyond.com/sheet-pdfs/wazic_92446074.pdf"


def test_character_import_service_follows_escaped_dndbeyond_pdf_link(monkeypatch) -> None:
    service = CharacterImportService()

    def fake_fetch(url: str):
        if url == "https://www.dndbeyond.com/profile/wazic/characters/92446074":
            return SimpleNamespace(
                content=(
                    b"<script>"
                    b'"pdfUrl":"https:\\\\/\\\\/www.dndbeyond.com\\\\/sheet-pdfs'
                    b'\\\\/wazic_92446074.pdf"'
                    b"</script>"
                ),
                content_type="text/html; charset=utf-8",
                final_url=url,
            )
        if url == "https://www.dndbeyond.com/sheet-pdfs/wazic_92446074.pdf":
            return SimpleNamespace(
                content=b"%PDF test",
                content_type="application/pdf",
                final_url=url,
            )
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(service, "_fetch_url", fake_fetch)
    monkeypatch.setattr(
        service,
        "_extract_pdf_bytes",
        lambda content: "Character Name: Ravenisis\nClass & Level: Cleric 6",
    )

    draft = service.import_url("https://www.dndbeyond.com/profile/wazic/characters/92446074")

    assert draft.name == "Ravenisis"
    assert draft.source == "https://www.dndbeyond.com/sheet-pdfs/wazic_92446074.pdf"


def test_character_import_controller_saves_character_and_campaign_reference(tmp_path) -> None:
    class StubImportService(CharacterImportService):
        def import_pdf(self, pdf_path: Path | str) -> CharacterImportDraft:
            return CharacterImportDraft(
                name="Lyra Thorn",
                level=3,
                hit_points=HitPoints(19, 24),
                source=str(pdf_path),
            )

    persistence = PersistenceService(JsonFileStore(tmp_path))
    persistence.save_campaign(Campaign("starter", "Starter"))
    controller = CharacterImportController(
        StubImportService(),
        CampaignService(),
        persistence,
    )

    result = controller.import_pdf_to_campaign("lyra.pdf", "starter")

    assert result.character.character_id == "lyra_thorn"
    assert persistence.load_character("lyra_thorn").name == "Lyra Thorn"
    assert persistence.load_campaign("starter").character_ids == ("lyra_thorn",)


def test_character_import_controller_saves_reviewed_draft(tmp_path) -> None:
    persistence = PersistenceService(JsonFileStore(tmp_path))
    persistence.save_campaign(Campaign("starter", "Starter"))
    controller = CharacterImportController(
        CharacterImportService(),
        CampaignService(),
        persistence,
    )

    result = controller.import_draft_to_campaign(
        CharacterImportDraft("Edited Name", hit_points=HitPoints(9, 9)),
        "starter",
    )

    assert result.character.character_id == "edited_name"
    assert persistence.load_character("edited_name").name == "Edited Name"
    assert persistence.load_campaign("starter").character_ids == ("edited_name",)


def test_character_import_controller_saves_url_import(tmp_path) -> None:
    class StubImportService(CharacterImportService):
        def import_url(self, url: str) -> CharacterImportDraft:
            return CharacterImportDraft(
                name="Lyra Thorn",
                level=3,
                hit_points=HitPoints(19, 24),
                source=url,
            )

    persistence = PersistenceService(JsonFileStore(tmp_path))
    persistence.save_campaign(Campaign("starter", "Starter"))
    controller = CharacterImportController(
        StubImportService(),
        CampaignService(),
        persistence,
    )

    result = controller.import_url_to_campaign("https://example.test/lyra", "starter")

    assert result.character.character_id == "lyra_thorn"
    assert persistence.load_character("lyra_thorn").name == "Lyra Thorn"
    assert persistence.load_campaign("starter").character_ids == ("lyra_thorn",)


def test_character_import_controller_generates_unique_character_ids(tmp_path) -> None:
    class StubImportService(CharacterImportService):
        def import_pdf(self, pdf_path: Path | str) -> CharacterImportDraft:
            return CharacterImportDraft(name="Lyra Thorn", hit_points=HitPoints(1, 1))

    persistence = PersistenceService(JsonFileStore(tmp_path))
    persistence.save_campaign(Campaign("starter", "Starter"))
    persistence.save_character(CharacterImportDraft("Lyra Thorn").to_character("lyra_thorn"))
    controller = CharacterImportController(
        StubImportService(),
        CampaignService(),
        persistence,
    )

    result = controller.import_pdf_to_campaign("lyra.pdf", "starter")

    assert result.character.character_id == "lyra_thorn_2"


def test_character_import_service_rejects_non_pdf(tmp_path) -> None:
    path = tmp_path / "sheet.txt"
    path.write_text(SHEET_TEXT, encoding="utf-8")

    with pytest.raises(CharacterImportError, match="requires a PDF"):
        CharacterImportService().import_pdf(path)


def test_character_import_service_rejects_non_http_urls() -> None:
    with pytest.raises(CharacterImportError, match="http or https"):
        CharacterImportService().import_url("file:///tmp/sheet.pdf")
