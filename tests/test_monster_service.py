from fractions import Fraction

import pytest

from dnd_combat_engine.models import AbilityScores, DamageType, HitPoints, Monster
from dnd_combat_engine.services import MonsterService


def make_monster(
    monster_id: str,
    name: str,
    challenge_rating: Fraction,
    resistant: bool = False,
    immune: bool = False,
) -> Monster:
    return Monster(
        monster_id=monster_id,
        name=name,
        armor_class=12,
        hit_points=HitPoints(current=5, maximum=5),
        abilities=AbilityScores(),
        challenge_rating=challenge_rating,
        damage_resistances=(DamageType.FIRE,) if resistant else (),
        damage_immunities=(DamageType.FIRE,) if immune else (),
    )


def test_monster_service_filters_by_challenge_range() -> None:
    monsters = [
        make_monster("ogre", "Ogre", Fraction(2)),
        make_monster("wolf", "Wolf", Fraction(1, 4)),
        make_monster("goblin", "Goblin", Fraction(1, 4)),
    ]

    result = MonsterService().by_challenge_range(monsters, maximum=Fraction(1, 2))

    assert [monster.monster_id for monster in result] == ["goblin", "wolf"]


def test_monster_service_rejects_invalid_challenge_range() -> None:
    with pytest.raises(ValueError):
        MonsterService().by_challenge_range([], minimum=2, maximum=1)


def test_monster_service_finds_resistant_or_immune_monsters() -> None:
    monsters = [
        make_monster("imp", "Imp", Fraction(1), resistant=True),
        make_monster("fire-elemental", "Fire Elemental", Fraction(5), immune=True),
        make_monster("wolf", "Wolf", Fraction(1, 4)),
    ]

    result = MonsterService().resistant_to(monsters, DamageType.FIRE)

    assert [monster.monster_id for monster in result] == ["imp", "fire-elemental"]

