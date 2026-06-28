"""Dice controller workflows."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dnd_combat_engine.services.dice_service import DiceService
from dnd_combat_engine.utils.dice import DiceRollResult


@dataclass(frozen=True, slots=True)
class DiceController:
    """UI-facing dice tray workflow coordinator."""

    dice_service: DiceService

    def roll(self, notation: str, rng: random.Random | None = None) -> DiceRollResult:
        """Roll dice notation."""
        return self.dice_service.roll(notation, rng=rng)

    def describe(self, notation: str) -> dict[str, int | float | str | None]:
        """Return display metadata for dice notation."""
        expression = self.dice_service.parse(notation)
        return {
            "notation": expression.notation,
            "minimum": expression.minimum(),
            "maximum": expression.maximum(),
            "average": expression.average(),
        }

