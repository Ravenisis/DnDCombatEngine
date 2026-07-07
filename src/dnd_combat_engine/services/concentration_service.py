"""Concentration lifecycle business operations."""

from __future__ import annotations

import random

from dnd_combat_engine.models import (
    Character,
    ConcentrationOutcome,
    ConcentrationResult,
    ConcentrationState,
    DurationKind,
    EffectDefinition,
    TargetReference,
)
from dnd_combat_engine.models.concentration import concentration_save_dc
from dnd_combat_engine.services.dice_service import DiceService


class ConcentrationService:
    """Start, replace, break, and check concentration effects."""

    def __init__(self, dice_service: DiceService | None = None) -> None:
        """Create a concentration service with a dice dependency."""
        self.dice_service = dice_service or DiceService()

    def start(
        self,
        caster: Character,
        effect: EffectDefinition,
        targets: tuple[TargetReference, ...] = (),
        current: ConcentrationState | None = None,
    ) -> ConcentrationResult:
        """Start concentration for an effect, replacing any current effect."""
        if effect.duration.kind != DurationKind.CONCENTRATION:
            raise ValueError(f"{effect.name} is not a concentration effect")
        state = ConcentrationState(
            caster_id=caster.character_id,
            effect_id=effect.effect_id,
            effect_name=effect.name,
            targets=targets,
            duration_text=effect.duration.text,
            rule_source=effect.rule_source,
        )
        if current is not None:
            return ConcentrationResult(
                outcome=ConcentrationOutcome.REPLACED,
                state=state,
                previous=current,
            )
        return ConcentrationResult(outcome=ConcentrationOutcome.STARTED, state=state)

    def break_concentration(self, current: ConcentrationState | None) -> ConcentrationResult:
        """Break concentration if an effect is active."""
        return ConcentrationResult(outcome=ConcentrationOutcome.BROKEN, previous=current)

    def check_after_damage(
        self,
        caster: Character,
        current: ConcentrationState,
        damage_taken: int,
        *,
        save_bonus: int = 0,
        rng: random.Random | None = None,
    ) -> ConcentrationResult:
        """Roll a Constitution save to maintain concentration after damage."""
        dc = concentration_save_dc(damage_taken)
        roll = self.dice_service.roll("1d20", rng=rng)
        total = roll.total + caster.abilities.modifier("constitution") + save_bonus
        if total >= dc:
            return ConcentrationResult(
                outcome=ConcentrationOutcome.MAINTAINED,
                state=current,
                save_dc=dc,
                save_total=total,
            )
        return ConcentrationResult(
            outcome=ConcentrationOutcome.BROKEN,
            previous=current,
            save_dc=dc,
            save_total=total,
        )

