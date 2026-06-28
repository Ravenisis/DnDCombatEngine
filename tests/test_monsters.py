from fractions import Fraction

import pytest

from dnd_combat_engine.models import (
    AbilityScores,
    CreatureSize,
    CreatureType,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    Monster,
    Weapon,
)


def make_monster() -> Monster:
    bite = Weapon(
        name="Bite",
        damage=DamageProfile((DamageComponent("1d6", DamageType.PIERCING),)),
    )
    return Monster(
        monster_id="wolf",
        name="Wolf",
        armor_class=13,
        hit_points=HitPoints(current=11, maximum=11),
        abilities=AbilityScores(strength=12, dexterity=15, constitution=12, wisdom=12),
        challenge_rating=Fraction(1, 4),
        size=CreatureSize.MEDIUM,
        creature_type=CreatureType.BEAST,
        speed={"walk": 40},
        actions=(bite,),
        senses=("passive Perception 13",),
        damage_resistances=(DamageType.COLD,),
    )


def test_monster_round_trips_to_plain_data() -> None:
    monster = make_monster()

    restored = Monster.from_dict(monster.to_dict())

    assert restored == monster
    assert restored.challenge_rating == Fraction(1, 4)
    assert restored.actions[0].damage.components[0].damage_type is DamageType.PIERCING


def test_monster_serializes_whole_number_challenge_rating() -> None:
    monster = Monster(
        monster_id="goblin",
        name="Goblin",
        armor_class=15,
        hit_points=HitPoints(current=7, maximum=7),
        abilities=AbilityScores(dexterity=14),
        challenge_rating=Fraction(1),
    )

    assert monster.to_dict()["challenge_rating"] == 1


def test_monster_rejects_invalid_values() -> None:
    kwargs = {
        "monster_id": "x",
        "name": "X",
        "armor_class": 10,
        "hit_points": HitPoints(current=1, maximum=1),
        "abilities": AbilityScores(),
        "challenge_rating": Fraction(0),
    }

    with pytest.raises(ValueError):
        Monster(**{**kwargs, "monster_id": ""})
    with pytest.raises(ValueError):
        Monster(**{**kwargs, "name": ""})
    with pytest.raises(ValueError):
        Monster(**{**kwargs, "armor_class": 0})
    with pytest.raises(ValueError):
        Monster(**{**kwargs, "challenge_rating": Fraction(-1)})
    with pytest.raises(ValueError):
        Monster(**{**kwargs, "speed": {"walk": -1}})

