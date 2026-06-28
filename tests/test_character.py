from dnd_combat_engine.models import (
    AbilityScores,
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
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
        resources={"hit_dice": 1},
    )

    restored = Character.from_dict(character.to_dict())

    assert restored == character
    assert restored.weapons[0].damage.components[0].damage_type is DamageType.PIERCING

