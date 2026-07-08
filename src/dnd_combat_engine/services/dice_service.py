"""Dice service facade."""

from __future__ import annotations

import random
import re

from dnd_combat_engine.utils.dice import DiceExpression, DiceRollResult

_TERM_RE = re.compile(r"[+-]?[^+-]+")


class DiceService:
    """Application-facing dice parser and roller."""

    def parse(self, notation: str) -> DiceExpression:
        """Parse dice notation into an expression."""
        return DiceExpression.parse(_normalized_notation(notation))

    def roll(self, notation: str, rng: random.Random | None = None) -> DiceRollResult:
        """Roll a dice notation string."""
        normalized = _normalized_notation(notation)
        try:
            return self.parse(normalized).roll(rng=rng)
        except ValueError:
            compound = _roll_compound(normalized, rng=rng)
            if compound is not None:
                return compound
            raise

    def average(self, notation: str) -> float:
        """Return the expected average for a dice notation string."""
        normalized = _normalized_notation(notation)
        try:
            return self.parse(normalized).average()
        except ValueError:
            compound = _average_compound(normalized)
            if compound is not None:
                return compound
            raise


def _normalized_notation(notation: str) -> str:
    return notation.strip().lower().replace(" ", "").replace("spellcasting_modifier", "0")


def _roll_compound(notation: str, rng: random.Random | None = None) -> DiceRollResult | None:
    if re.fullmatch(r"[+-]?\d+", notation):
        value = int(notation)
        return DiceRollResult(notation=notation, total=value, rolls=(), kept=(), modifier=value)
    terms = _compound_terms(notation)
    if terms is None:
        return None
    total = 0
    rolls: list[int] = []
    kept: list[int] = []
    modifier = 0
    for sign, term in terms:
        if "d" in term:
            result = DiceExpression.parse(term).roll(rng=rng)
            total += sign * result.total
            rolls.extend(sign * roll for roll in result.rolls)
            kept.extend(sign * roll for roll in result.kept)
        else:
            value = sign * int(term)
            total += value
            modifier += value
    return DiceRollResult(
        notation=notation,
        total=total,
        rolls=tuple(rolls),
        kept=tuple(kept),
        modifier=modifier,
    )


def _average_compound(notation: str) -> float | None:
    if re.fullmatch(r"[+-]?\d+", notation):
        return float(int(notation))
    terms = _compound_terms(notation)
    if terms is None:
        return None
    total = 0.0
    for sign, term in terms:
        if "d" in term:
            total += sign * DiceExpression.parse(term).average()
        else:
            total += sign * int(term)
    return total


def _compound_terms(notation: str) -> tuple[tuple[int, str], ...] | None:
    raw_terms = _TERM_RE.findall(notation)
    if len(raw_terms) < 2 or "".join(raw_terms) != notation:
        return None
    terms: list[tuple[int, str]] = []
    for raw in raw_terms:
        sign = -1 if raw.startswith("-") else 1
        term = raw[1:] if raw.startswith(("+", "-")) else raw
        if not term or not re.fullmatch(r"(?:\d*d\d+|\d+)", term):
            return None
        terms.append((sign, term))
    return tuple(terms)
