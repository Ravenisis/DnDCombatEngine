from dnd_combat_engine.controllers import CombatController
from dnd_combat_engine.models import (
    ActionCost,
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    EffectDefinition,
    EffectKind,
    HitPoints,
    ResourcePool,
    TargetKind,
    TargetProfile,
    TargetReference,
    TurnEconomy,
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


def test_combat_controller_resolves_unified_combat_action() -> None:
    controller = CombatController(CombatService())
    target = TargetReference("goblin", "Goblin", TargetKind.MONSTER, "goblin")
    action = EffectDefinition(
        effect_id="guiding-bolt-damage",
        name="Guiding Bolt",
        effect_kind=EffectKind.DAMAGE,
        target_profile=TargetProfile.ONE_CREATURE,
        action_cost=ActionCost.ACTION,
        resource_cost="spell_slot_1",
        dice="4d6",
    )
    economy = TurnEconomy()
    resources = {"spell_slot_1": ResourcePool("spell_slot_1", current=2, maximum=2)}

    result = controller.resolve_action(
        actor_name="Ravenisis",
        action=action,
        targets=(target,),
        total=17,
        detail="Attack roll hit AC 15.",
        economy=economy,
        resources=resources,
    )

    assert result.action_spent is True
    assert result.resource_spent == "spell_slot_1"
    assert economy.action_used is True
    assert resources["spell_slot_1"].current == 1
    assert result.messages == (
        "Ravenisis resolves Guiding Bolt on Goblin [damage]. "
        "Total 17. Spent spell_slot_1. Dice 4d6. Attack roll hit AC 15.",
    )
