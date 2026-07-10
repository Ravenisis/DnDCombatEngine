from dnd_combat_engine.models import Character, HitPoints, ResourcePool
from dnd_combat_engine.models.spell_slots import (
    ensure_spell_slot_resources,
    ensure_spell_slot_resources_for_level,
    inferred_spell_slots,
)


def test_spell_slots_are_inferred_for_imported_cleric_features() -> None:
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(12, 12),
        level=6,
        features=(
            "Cleric 6",
            "Cantrips: Light, Sacred Flame, Thaumaturgy",
            "Domain Spells: Bless, Cure Wounds, Revivify",
        ),
    )

    assert inferred_spell_slots(character) == {1: 4, 2: 3, 3: 3}
    assert ensure_spell_slot_resources(character) is True
    assert character.resources["spell_slot_1"].current == 4
    assert character.resources["spell_slot_2"].maximum == 3
    assert character.resources["spell_slot_3"].current == 3


def test_spell_slot_repair_does_not_reset_existing_spent_slots() -> None:
    character = Character(
        "cleric",
        "Cleric",
        HitPoints(12, 12),
        level=3,
        features=("Cleric 3",),
    )
    ensure_spell_slot_resources(character)
    character.resources["spell_slot_1"].current = 0

    assert ensure_spell_slot_resources(character) is False
    assert character.resources["spell_slot_1"].current == 0


def test_spell_slot_repair_upgrades_incomplete_legacy_slot_maps() -> None:
    character = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        level=6,
        features=("Cleric 6",),
        resources={
            "spell_slot_1": ResourcePool("spell_slot_1", current=1, maximum=2),
        },
    )

    assert ensure_spell_slot_resources(character) is True

    assert character.resources["spell_slot_1"].maximum == 4
    assert character.resources["spell_slot_1"].current == 3
    assert character.resources["spell_slot_2"].maximum == 3
    assert character.resources["spell_slot_3"].maximum == 3


def test_spell_slot_repair_uses_explicit_cast_level_when_sheet_text_is_missing() -> None:
    character = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(63, 63),
        level=6,
    )

    assert ensure_spell_slot_resources(character) is False
    assert ensure_spell_slot_resources_for_level(character, 2) is True

    assert character.resources["spell_slot_1"].maximum == 4
    assert character.resources["spell_slot_2"].maximum == 3
    assert character.resources["spell_slot_2"].current == 3
