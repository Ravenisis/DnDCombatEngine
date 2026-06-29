from pathlib import Path

import pytest

from dnd_combat_engine.controllers import CharacterImportController
from dnd_combat_engine.models import Campaign, HitPoints
from dnd_combat_engine.models.imports import CharacterImportDraft
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import (
    CampaignService,
    CharacterImportError,
    CharacterImportService,
    PersistenceService,
)

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

