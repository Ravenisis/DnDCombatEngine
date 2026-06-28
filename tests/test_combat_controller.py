from dnd_combat_engine.controllers import CombatController
from dnd_combat_engine.models import (
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    Weapon,
)
from dnd_combat_engine.services import CombatService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def test_combat_controller_builds_and_resolves_weapon_attack() -> None:
    attacker = Character("fighter", "Bran", HitPoints(12, 12))
    target = Character("goblin", "Goblin", HitPoints(7, 7))
    weapon = Weapon(
        "Longsword",
        DamageProfile((DamageComponent("1d8", DamageType.SLASHING),)),
    )
    controller = CombatController(CombatService())

    result = controller.attack_with_weapon(
        attacker=attacker,
        target=target,
        weapon=weapon,
        target_armor_class=15,
        attack_bonus=3,
        damage_bonus=2,
        rng=SequenceRng([12, 4]),  # type: ignore[arg-type]
    )

    assert result.hit is True
    assert result.attack_total == 15
    assert result.damage_total == 6
    assert target.hit_points.current == 1

