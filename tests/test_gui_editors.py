import pytest

from dnd_combat_engine.app import create_app
from dnd_combat_engine.gui.editors import (
    add_character_to_campaign,
    add_character_to_encounter,
    add_encounter_to_campaign,
    add_monster_to_encounter,
    advance_encounter_round,
    complete_encounter,
    remove_character_from_campaign,
    remove_encounter_from_campaign,
    remove_participant_from_encounter,
    start_encounter,
)
from dnd_combat_engine.models import Campaign, Encounter, EncounterStatus
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.utils.paths import initialize_user_data


def test_campaign_editor_helpers_update_and_save_references(tmp_path) -> None:
    data_root = initialize_user_data(tmp_path / "data")
    store = JsonFileStore(data_root)
    store.save("campaigns", "empty", Campaign("empty", "Empty").to_dict())
    app = create_app(data_root)

    assert add_character_to_campaign(app, "empty", "vale") == "Added character Vale to Empty."
    assert add_encounter_to_campaign(
        app,
        "empty",
        "roadside_ambush",
    ) == "Added encounter Roadside Ambush to Empty."

    campaign = Campaign.from_dict(store.load("campaigns", "empty"))
    assert campaign.character_ids == ("vale",)
    assert campaign.encounter_ids == ("roadside_ambush",)

    assert remove_character_from_campaign(app, "empty", "vale") == (
        "Removed character vale from Empty."
    )
    assert remove_encounter_from_campaign(app, "empty", "roadside_ambush") == (
        "Removed encounter roadside_ambush from Empty."
    )
    campaign = Campaign.from_dict(store.load("campaigns", "empty"))
    assert campaign.character_ids == ()
    assert campaign.encounter_ids == ()


def test_encounter_editor_helpers_update_participants_and_lifecycle(tmp_path) -> None:
    data_root = initialize_user_data(tmp_path / "data")
    store = JsonFileStore(data_root)
    store.save("encounters", "editor", Encounter("editor", "Editor").to_dict())
    app = create_app(data_root)

    assert add_character_to_encounter(app, "editor", "vale") == "Added Vale to Editor."
    assert add_monster_to_encounter(app, "editor", "goblin", quantity=2) == (
        "Added 2 Goblin to Editor."
    )

    encounter = Encounter.from_dict(store.load("encounters", "editor"))
    assert [participant.participant_id for participant in encounter.participants] == [
        "vale",
        "goblin",
    ]

    assert remove_participant_from_encounter(app, "editor", "goblin") == (
        "Removed participant goblin from Editor."
    )
    assert start_encounter(app, "editor") == "Started Editor."
    assert advance_encounter_round(app, "editor") == "Advanced Editor to round 2."
    assert complete_encounter(app, "editor") == "Completed Editor."
    assert (
        Encounter.from_dict(store.load("encounters", "editor")).status
        is EncounterStatus.COMPLETED
    )


def test_encounter_editor_rejects_invalid_monster_quantity(tmp_path) -> None:
    data_root = initialize_user_data(tmp_path / "data")
    store = JsonFileStore(data_root)
    store.save("encounters", "editor", Encounter("editor", "Editor").to_dict())
    app = create_app(data_root)

    with pytest.raises(ValueError):
        add_monster_to_encounter(app, "editor", "goblin", quantity=0)
