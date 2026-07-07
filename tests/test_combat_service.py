from __future__ import annotations

from dataclasses import replace

from dnd_combat_engine.engine import AttackRequest
from dnd_combat_engine.engine.events import EngineEvent
from dnd_combat_engine.models import (
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    Weapon,
)
from dnd_combat_engine.rules import FeatureEngine
from dnd_combat_engine.services import CombatService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


class AttackBonusFeature:
    name = "attack-bonus"

    def applies_to(self, event: EngineEvent) -> bool:
        return event.name == "attack.started"

    def handle(self, event: EngineEvent) -> EngineEvent:
        request = event.payload["request"]
        assert isinstance(request, AttackRequest)
        return EngineEvent(event.name, {"request": replace(request, attack_bonus=4)})


class FinishedRecorder:
    name = "finished-recorder"

    def __init__(self) -> None:
        self.finished: list[EngineEvent] = []

    def applies_to(self, event: EngineEvent) -> bool:
        return event.name == "attack.finished"

    def handle(self, event: EngineEvent) -> EngineEvent:
        self.finished.append(event)
        return event


def make_character(character_id: str, name: str, hp: int = 10) -> Character:
    return Character(character_id=character_id, name=name, hit_points=HitPoints(hp, hp))


def make_weapon(dice: str = "1d8") -> Weapon:
    return Weapon(
        name="Longsword",
        damage=DamageProfile((DamageComponent(dice, DamageType.SLASHING),)),
    )


def test_missed_attack_does_not_apply_damage() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(make_character("attacker", "Attacker"), target, make_weapon(), 15)

    result = CombatService().resolve_attack(request, rng=SequenceRng([5]))  # type: ignore[arg-type]

    assert result.hit is False
    assert result.damage_total == 0
    assert target.hit_points.current == 10


def test_hit_rolls_damage_and_applies_it_to_target() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        make_character("attacker", "Attacker"),
        target,
        make_weapon(),
        target_armor_class=15,
        attack_bonus=2,
        damage_bonus=2,
    )

    result = CombatService().resolve_attack(request, rng=SequenceRng([13, 4]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.critical is False
    assert result.attack_total == 15
    assert result.damage_by_type == {DamageType.SLASHING: 4}
    assert result.damage_total == 6
    assert result.damage_applied == 6
    assert target.hit_points.current == 4


def test_natural_twenty_hits_and_doubles_damage_dice() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(make_character("attacker", "Attacker"), target, make_weapon(), 30)

    result = CombatService().resolve_attack(request, rng=SequenceRng([20, 3, 4]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.critical is True
    assert result.critical_miss is False
    assert result.damage_total == 7
    assert result.damage_rolls[0].roll.notation == "2d8"


def test_natural_one_misses_even_with_high_bonus() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        make_character("attacker", "Attacker"),
        target,
        make_weapon(),
        target_armor_class=5,
        attack_bonus=99,
    )

    result = CombatService().resolve_attack(request, rng=SequenceRng([1]))  # type: ignore[arg-type]

    assert result.hit is False
    assert result.critical_miss is True
    assert result.attack_total == 100


def test_feature_engine_can_modify_attack_before_roll_and_observe_finish() -> None:
    target = make_character("target", "Target")
    recorder = FinishedRecorder()
    service = CombatService(feature_engine=FeatureEngine([AttackBonusFeature(), recorder]))
    request = AttackRequest(make_character("attacker", "Attacker"), target, make_weapon(), 12)

    result = service.resolve_attack(request, rng=SequenceRng([8, 5]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.attack_total == 12
    assert recorder.finished[0].payload["result"] == result
