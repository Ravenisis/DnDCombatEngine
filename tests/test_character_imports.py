from pathlib import Path
from types import SimpleNamespace

import pytest

from dnd_combat_engine.controllers import CharacterImportController
from dnd_combat_engine.models import Campaign, HitPoints, RuleSource
from dnd_combat_engine.models.imports import CharacterImportDraft
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import (
    CampaignService,
    CharacterImportError,
    CharacterImportService,
    PersistenceService,
)
from dnd_combat_engine.services.character_import_service import _extract_pdf_literal_text

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
    assert [item.name for item in draft.inventory] == [
        "Bag of Holding",
        "Potion of Healing (Greater",
    ]
    assert draft.currency.pp == 298
    assert draft.currency.gp == 9


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
