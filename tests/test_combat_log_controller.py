from dnd_combat_engine.controllers import CombatLogController
from dnd_combat_engine.engine import AttackRequest, AttackResult
from dnd_combat_engine.models import (
    Character,
    CombatLog,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    Weapon,
)
from dnd_combat_engine.services import CombatLogService, CombatService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def make_result() -> AttackResult:
    attacker = Character("fighter", "Bran", HitPoints(12, 12))
    target = Character("goblin", "Goblin", HitPoints(7, 7))
    weapon = Weapon(
        "Longsword",
        DamageProfile((DamageComponent("1d8", DamageType.SLASHING),)),
    )
    request = AttackRequest(attacker, target, weapon, target_armor_class=15, attack_bonus=3)
    return CombatService().resolve_attack(request, rng=SequenceRng([12, 4]))  # type: ignore[arg-type]


def test_combat_log_controller_records_attack() -> None:
    controller = CombatLogController(CombatLogService())

    log = controller.record_attack(CombatLog(), make_result())

    assert "Bran hits Goblin" in log.entries[0].message
    assert controller.latest(log, 1) == log.entries


def test_combat_log_records_critical_miss() -> None:
    controller = CombatLogController(CombatLogService())
    attacker = Character("fighter", "Bran", HitPoints(12, 12))
    target = Character("goblin", "Goblin", HitPoints(7, 7))
    weapon = Weapon(
        "Longsword",
        DamageProfile((DamageComponent("1d8", DamageType.SLASHING),)),
    )
    request = AttackRequest(attacker, target, weapon, target_armor_class=5, attack_bonus=99)
    result = CombatService().resolve_attack(request, rng=SequenceRng([1]))  # type: ignore[arg-type]

    log = controller.record_attack(CombatLog(), result)

    assert "Bran critically misses Goblin" in log.entries[0].message
    assert log.entries[0].metadata["critical_miss"] is True
