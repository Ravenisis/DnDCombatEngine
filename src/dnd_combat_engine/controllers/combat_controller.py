"""Combat controller workflows."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from dnd_combat_engine.engine.attacks import AttackRequest, AttackResult
from dnd_combat_engine.models.action_economy import TurnEconomy
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.combat_log import CombatLogEntry, CombatLogEntryType
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
class CombatActionRequest:
    """One GUI-selected action ready for rules resolution."""

    actor_id: str
    actor_name: str
    action: EffectDefinition
    targets: tuple[TargetReference, ...] = ()
    total: int | None = None
    detail: str = ""
    economy: TurnEconomy | None = None
    resources: dict[str, ResourcePool] | None = None

    def __post_init__(self) -> None:
        """Validate the selected actor and action context."""
        if not self.actor_id:
            raise ValueError("actor_id is required")
        if not self.actor_name:
            raise ValueError("actor_name is required")


@dataclass(frozen=True, slots=True)
class CombatActionOutcome:
    """Resolved action output shared by GUI, persistence, and logs."""

    request: CombatActionRequest
    resolution: EffectResolutionResult
    log_entries: tuple[CombatLogEntry, ...]

    @property
    def messages(self) -> tuple[str, ...]:
        """Return player-facing action messages."""
        return self.resolution.messages

    @property
    def message(self) -> str:
        """Return the first player-facing action message."""
        return self.messages[0] if self.messages else ""


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

    def execute_action(self, request: CombatActionRequest) -> CombatActionOutcome:
        """Run actor, target, resource, resolver, and log generation in one loop."""
        resolution = self.resolve_action(
            actor_name=request.actor_name,
            action=request.action,
            targets=request.targets,
            total=request.total,
            detail=request.detail,
            economy=request.economy,
            resources=request.resources,
        )
        entries = tuple(
            CombatLogEntry(
                message=message,
                entry_type=_log_entry_type(request.action),
                metadata={
                    "actor_id": request.actor_id,
                    "action_id": request.action.effect_id,
                    "target_ids": [target.target_id for target in request.targets],
                    "resource_spent": resolution.resource_spent,
                    "action_spent": resolution.action_spent,
                },
            )
            for message in resolution.messages
        )
        return CombatActionOutcome(request=request, resolution=resolution, log_entries=entries)

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


def _log_entry_type(action: EffectDefinition) -> CombatLogEntryType:
    match action.effect_kind.value:
        case "attack":
            return CombatLogEntryType.ATTACK
        case "damage":
            return CombatLogEntryType.DAMAGE
        case "healing":
            return CombatLogEntryType.HEALING
        case _:
            return CombatLogEntryType.SYSTEM
