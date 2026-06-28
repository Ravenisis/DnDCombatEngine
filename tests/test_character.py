from dnd_combat_engine.models import (
    AbilityScores,
    Character,
    Condition,
    ConditionName,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    ResourcePool,
    Weapon,
)


def test_character_round_trips_to_plain_data() -> None:
    rapier = Weapon(
        name="Rapier",
        damage=DamageProfile((DamageComponent("1d8", DamageType.PIERCING),)),
        properties=("finesse",),
    )
    character = Character(
        character_id="rogue-1",
        name="Vale",
        hit_points=HitPoints(current=9, maximum=12, temporary=4),
        abilities=AbilityScores(dexterity=16),
        weapons=(rapier,),
        features=("Sneak Attack",),
        conditions=(Condition(ConditionName.POISONED, remaining_rounds=2),),
        resources={"hit_dice": ResourcePool("hit_dice", current=1, maximum=1)},
    )

    restored = Character.from_dict(character.to_dict())

    assert restored == character
    assert restored.weapons[0].damage.components[0].damage_type is DamageType.PIERCING


def test_character_loads_legacy_condition_and_resource_shapes() -> None:
    character = Character.from_dict(
        {
            "character_id": "legacy-1",
            "name": "Legacy",
            "hit_points": {"current": 8, "maximum": 8, "temporary": 0},
            "abilities": AbilityScores().to_dict(),
            "conditions": ["prone"],
            "resources": {"hit_dice": 1},
        }
    )

    assert character.conditions == (Condition(ConditionName.PRONE),)
    assert character.resources["hit_dice"] == ResourcePool("hit_dice", 1, 1)
