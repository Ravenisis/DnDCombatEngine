"""Dice service facade."""

from __future__ import annotations

import random

from dnd_combat_engine.utils.dice import DiceExpression, DiceRollResult


class DiceService:
    """Application-facing dice parser and roller."""

    def parse(self, notation: str) -> DiceExpression:
        """Parse dice notation into an expression."""
        return DiceExpression.parse(notation)

    def roll(self, notation: str, rng: random.Random | None = None) -> DiceRollResult:
        """Roll a dice notation string."""
        return self.parse(notation).roll(rng=rng)

    def average(self, notation: str) -> float:
        """Return the expected average for a dice notation string."""
        return self.parse(notation).average()

