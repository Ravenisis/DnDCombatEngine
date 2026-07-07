"""Combat controller workflows."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from dnd_combat_engine.engine.attacks import AttackRequest, AttackResult
from dnd_combat_engine.models.action_economy import TurnEconomy
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.effects import EffectDefinition, TargetReference
from dnd_combat_engine.models.equipment import Weapon
from dnd_combat_engine.models.resources import ResourcePool
from dnd_combat_engine.rules.effect_resolver import (
    EffectPlan,
    EffectResolutionResult,
    EffectResolver,
)
from dnd_combat_engine.services.combat_service import CombatService


@dataclass(frozen=True, slots=True)
class CombatController:
    """UI-facing combat workflow coordinator."""

    combat_service: CombatService
    effect_resolver: EffectResolver = field(default_factory=EffectResolver)

    def resolve_action(
        self,
        *,
        actor_name: str,
        action: EffectDefinition,
        targets: tuple[TargetReference, ...] = (),
        total: int | None = None,
        detail: str = "",
        economy: TurnEconomy | None = None,
        resources: dict[str, ResourcePool] | None = None,
    ) -> EffectResolutionResult:
        """Resolve one complete combat action through the shared effect pipeline."""
        plan = EffectPlan(
            actor_name=actor_name,
            definition=action,
            targets=targets,
            total=total,
            detail=detail,
        )
        return self.effect_resolver.resolve(plan, economy=economy, resources=resources)

    def resolve_action_plan(
        self,
        plan: EffectPlan,
        *,
        economy: TurnEconomy | None = None,
        resources: dict[str, ResourcePool] | None = None,
    ) -> EffectResolutionResult:
        """Resolve a prebuilt combat action plan through the shared effect pipeline."""
        return self.effect_resolver.resolve(plan, economy=economy, resources=resources)

    def attack_with_weapon(
        self,
        attacker: Character,
        target: Character,
        weapon: Weapon,
        target_armor_class: int,
        attack_bonus: int = 0,
        damage_bonus: int = 0,
        active_features: tuple[str, ...] = (),
        rng: random.Random | None = None,
    ) -> AttackResult:
        """Build and resolve a weapon attack request."""
        request = AttackRequest(
            attacker=attacker,
            target=target,
            weapon=weapon,
            target_armor_class=target_armor_class,
            attack_bonus=attack_bonus,
            damage_bonus=damage_bonus,
            active_features=active_features,
        )
        return self.combat_service.resolve_attack(request, rng=rng)
