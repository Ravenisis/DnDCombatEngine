"""Reusable target and effect resolution helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from dnd_combat_engine.models import (
    EffectDefinition,
    EffectResolution,
    ResourcePool,
    TargetReference,
    TurnEconomy,
)


@dataclass(frozen=True, slots=True)
class EffectPlan:
    """The resolved player choices needed to execute an effect."""

    actor_name: str
    definition: EffectDefinition
    targets: tuple[TargetReference, ...] = field(default_factory=tuple)
    total: int | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        """Validate effect plan identity."""
        if not self.actor_name:
            raise ValueError("actor name is required")


@dataclass(frozen=True, slots=True)
class EffectResolutionResult:
    """Result of resolving a rule effect plan."""

    resolutions: tuple[EffectResolution, ...]
    resource_spent: str | None = None
    action_spent: bool = False

    @property
    def messages(self) -> tuple[str, ...]:
        """Return player-facing resolution messages."""
        return tuple(resolution.message() for resolution in self.resolutions)


class EffectResolver:
    """Validate and explain effect plans before concrete state mutation."""

    def resolve(
        self,
        plan: EffectPlan,
        *,
        economy: TurnEconomy | None = None,
        resources: dict[str, ResourcePool] | None = None,
    ) -> EffectResolutionResult:
        """Resolve a plan into explainable effect summaries."""
        definition = plan.definition
        if definition.requires_target and not plan.targets:
            raise ValueError(f"{definition.name} requires at least one target")
        action_spent = False
        if economy is not None:
            action_spent = economy.spend(definition.action_cost)
            if not action_spent:
                raise ValueError(f"{definition.action_cost.value} is already spent")
        resource_spent = self._spend_resource(definition.resource_cost, resources)
        targets = plan.targets or (None,)
        resolutions = tuple(
            EffectResolution(
                source_name=plan.actor_name,
                effect_name=definition.name,
                effect_kind=definition.effect_kind,
                target=target,
                total=plan.total,
                detail=_resolution_detail(plan, resource_spent),
            )
            for target in targets
        )
        return EffectResolutionResult(
            resolutions=resolutions,
            resource_spent=resource_spent,
            action_spent=action_spent,
        )

    def _spend_resource(
        self,
        resource_cost: str | None,
        resources: dict[str, ResourcePool] | None,
    ) -> str | None:
        if resource_cost is None:
            return None
        if resources is None or resource_cost not in resources:
            raise ValueError(f"resource {resource_cost} is unavailable")
        if not resources[resource_cost].expend():
            raise ValueError(f"resource {resource_cost} is depleted")
        return resource_cost


def _resolution_detail(plan: EffectPlan, resource_spent: str | None) -> str:
    details = []
    if resource_spent:
        details.append(f"Spent {resource_spent}.")
    if plan.definition.dice:
        details.append(f"Dice {plan.definition.dice}.")
    if plan.detail:
        details.append(plan.detail)
    return " ".join(details)

