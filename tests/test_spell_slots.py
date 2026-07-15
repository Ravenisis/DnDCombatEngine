from dnd_combat_engine.models import (
    Character,
    HitPoints,
    ResourcePool,
    ensure_channel_divinity_resource,
    inferred_channel_divinity_uses,
)
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


def test_channel_divinity_resource_is_inferred_and_upgraded_without_refilling() -> None:
    character = Character(
        "cleric",
        "Cleric",
        HitPoints(20, 20),
        level=6,
        character_class="Cleric 6",
        features=("Channel Divinity: Turn Undead",),
        resources={"channel_divinity": ResourcePool("channel_divinity", 0, 1)},
    )

    assert inferred_channel_divinity_uses(character) == 2
    assert ensure_channel_divinity_resource(character) is True
    assert character.resources["channel_divinity"].maximum == 2
    assert character.resources["channel_divinity"].current == 1
    assert ensure_channel_divinity_resource(character) is False


def test_channel_divinity_is_not_added_without_the_feature() -> None:
    character = Character("fighter", "Fighter", HitPoints(12, 12), level=6)

    assert inferred_channel_divinity_uses(character) == 0
    assert ensure_channel_divinity_resource(character) is False


def test_channel_divinity_resource_is_created_for_supported_classes() -> None:
    cleric = Character(
        "cleric",
        "Cleric",
        HitPoints(10, 10),
        level=2,
        character_class="Cleric 2",
        features=("Channel Divinity: Turn Undead",),
    )
    paladin = Character(
        "paladin",
        "Paladin",
        HitPoints(10, 10),
        level=3,
        character_class="Paladin 3",
        features=("Channel Divinity: Sacred Weapon",),
    )
    other = Character(
        "other",
        "Other",
        HitPoints(10, 10),
        features=("Channel Divinity: Custom",),
    )

    assert ensure_channel_divinity_resource(cleric) is True
    assert cleric.resources["channel_divinity"].current == 1
    assert inferred_channel_divinity_uses(paladin) == 1
    assert inferred_channel_divinity_uses(other) == 1
