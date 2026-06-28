"""Combat workflow service."""

from __future__ import annotations

import random
from dataclasses import replace

from dnd_combat_engine.engine.attacks import AttackRequest, AttackResult, DamageRoll
from dnd_combat_engine.engine.events import AttackFinishedEvent, AttackStartedEvent
from dnd_combat_engine.rules.feature_engine import FeatureEngine
from dnd_combat_engine.services.dice_service import DiceService
from dnd_combat_engine.utils.dice import DiceExpression


class CombatService:
    """Resolve combat workflows without embedding class feature rules."""

    def __init__(
        self,
        dice_service: DiceService | None = None,
        feature_engine: FeatureEngine | None = None,
    ) -> None:
        """Create a combat service with dice and feature dependencies."""
        self.dice_service = dice_service or DiceService()
        self.feature_engine = feature_engine or FeatureEngine()

    def resolve_attack(
        self,
        request: AttackRequest,
        rng: random.Random | None = None,
    ) -> AttackResult:
        """Resolve an attack request, apply damage on hit, and return the result."""
        started = self.feature_engine.process(AttackStartedEvent({"request": request}))
        final_request = started.payload.get("request", request)
        if not isinstance(final_request, AttackRequest):
            raise TypeError("attack.started payload request must be an AttackRequest")

        attack_roll = self.dice_service.roll(final_request.attack_dice, rng=rng)
        attack_bonus_rolls = tuple(
            self.dice_service.roll(notation, rng=rng)
            for notation in final_request.attack_bonus_dice
        )
        natural = max(attack_roll.kept)
        attack_total = natural + final_request.attack_bonus + sum(
            roll.total for roll in attack_bonus_rolls
        )
        hit = natural == 20 or (natural != 1 and attack_total >= final_request.target_armor_class)
        critical = hit and natural >= final_request.critical_threshold
        damage_rolls = self._roll_damage(final_request, critical=critical, rng=rng) if hit else ()
        preliminary = AttackResult(
            request=final_request,
            attack_roll=attack_roll,
            attack_total=attack_total,
            hit=hit,
            critical=critical,
            attack_bonus_rolls=attack_bonus_rolls,
            damage_rolls=damage_rolls,
            damage_bonus=final_request.damage_bonus if hit else 0,
        )
        damage_applied = (
            final_request.target.hit_points.apply_damage(preliminary.damage_total) if hit else 0
        )
        result = replace(preliminary, damage_applied=damage_applied)
        self.feature_engine.process(
            AttackFinishedEvent({"request": final_request, "result": result})
        )
        return result

    def _roll_damage(
        self,
        request: AttackRequest,
        critical: bool,
        rng: random.Random | None,
    ) -> tuple[DamageRoll, ...]:
        rolls = []
        components = (*request.weapon.damage.components, *request.extra_damage)
        for component in components:
            notation = _critical_notation(component.dice) if critical else component.dice
            rolls.append(
                DamageRoll(component.damage_type, self.dice_service.roll(notation, rng=rng))
            )
        return tuple(rolls)


def _critical_notation(notation: str) -> str:
    expression = DiceExpression.parse(notation)
    doubled = replace(expression, count=expression.count * 2)
    return doubled.notation
