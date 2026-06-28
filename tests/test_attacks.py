from dataclasses import replace

import pytest

from dnd_combat_engine.engine import AttackRequest
from dnd_combat_engine.models import (
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    Weapon,
)


def make_character(character_id: str, name: str, hp: int = 10) -> Character:
    return Character(character_id=character_id, name=name, hit_points=HitPoints(hp, hp))


def make_weapon() -> Weapon:
    return Weapon(
        name="Rapier",
        damage=DamageProfile((DamageComponent("1d8", DamageType.PIERCING),)),
        properties=("finesse",),
    )


def test_attack_request_uses_advantage_or_disadvantage_dice() -> None:
    base = AttackRequest(make_character("a", "A"), make_character("b", "B"), make_weapon(), 12)

    assert base.attack_dice == "1d20"
    assert replace(base, advantage=True).attack_dice == "2d20kh1"
    assert replace(base, disadvantage=True).attack_dice == "2d20kl1"
    assert replace(base, advantage=True, disadvantage=True).attack_dice == "1d20"


def test_attack_request_validates_bounds() -> None:
    attacker = make_character("a", "A")
    target = make_character("b", "B")
    weapon = make_weapon()

    with pytest.raises(ValueError):
        AttackRequest(attacker, target, weapon, 0)
    with pytest.raises(ValueError):
        AttackRequest(attacker, target, weapon, 12, critical_threshold=1)
