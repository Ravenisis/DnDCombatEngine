"""Dice parser and roller."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from itertools import product
from typing import Self

_DICE_RE = re.compile(
    r"^(?P<count>\d*)d(?P<sides>\d+)"
    r"(?:(?P<selector>kh|kl|dh|dl)(?P<select_count>\d+))?"
    r"(?P<explode>!)?"
    r"(?:(?P<reroll>r(?:<=|>=|<|>|=)?\d+))?"
    r"(?P<modifier>[+-]\d+)?$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class DiceRollResult:
    """The detailed result of a dice roll."""

    notation: str
    total: int
    rolls: tuple[int, ...]
    kept: tuple[int, ...]
    modifier: int = 0


@dataclass(frozen=True, slots=True)
class DiceExpression:
    """Parsed dice notation with rolling and statistics helpers."""

    count: int
    sides: int
    modifier: int = 0
    keep_highest: int | None = None
    keep_lowest: int | None = None
    drop_highest: int | None = None
    drop_lowest: int | None = None
    explode: bool = False
    reroll_threshold: int | None = None

    def __post_init__(self) -> None:
        """Validate dice expression fields."""
        if self.count < 1:
            raise ValueError("dice count must be at least 1")
        if self.sides < 2:
            raise ValueError("dice must have at least 2 sides")
        selectors = [
            self.keep_highest,
            self.keep_lowest,
            self.drop_highest,
            self.drop_lowest,
        ]
        if sum(selector is not None for selector in selectors) > 1:
            raise ValueError("cannot combine keep/drop selectors")
        keep_count = next((selector for selector in selectors if selector is not None), None)
        if keep_count is not None and not 1 <= keep_count <= self.count:
            raise ValueError("selector count must be between 1 and dice count")
        if self.reroll_threshold is not None and not 1 <= self.reroll_threshold <= self.sides:
            raise ValueError("reroll threshold must be within die sides")

    @property
    def notation(self) -> str:
        """Return normalized dice notation."""
        keep = ""
        if self.keep_highest is not None:
            keep = f"kh{self.keep_highest}"
        if self.keep_lowest is not None:
            keep = f"kl{self.keep_lowest}"
        if self.drop_highest is not None:
            keep = f"dh{self.drop_highest}"
        if self.drop_lowest is not None:
            keep = f"dl{self.drop_lowest}"
        explode = "!" if self.explode else ""
        reroll = f"r<={self.reroll_threshold}" if self.reroll_threshold is not None else ""
        modifier = f"{self.modifier:+d}" if self.modifier else ""
        return f"{self.count}d{self.sides}{keep}{explode}{reroll}{modifier}"

    @classmethod
    def parse(cls, notation: str) -> Self:
        """Parse supported dice notation."""
        compact = notation.strip().lower().replace(" ", "")
        match = _DICE_RE.match(compact)
        if not match:
            raise ValueError(f"unsupported dice notation: {notation}")
        count = int(match.group("count") or "1")
        sides = int(match.group("sides"))
        keep_highest = keep_lowest = drop_highest = drop_lowest = None
        selector = match.group("selector")
        select_count = int(match.group("select_count")) if selector else None
        if selector == "kh":
            keep_highest = select_count
        elif selector == "kl":
            keep_lowest = select_count
        elif selector == "dh":
            drop_highest = select_count
        elif selector == "dl":
            drop_lowest = select_count
        return cls(
            count=count,
            sides=sides,
            modifier=int(match.group("modifier") or "0"),
            keep_highest=keep_highest,
            keep_lowest=keep_lowest,
            drop_highest=drop_highest,
            drop_lowest=drop_lowest,
            explode=bool(match.group("explode")),
            reroll_threshold=_parse_reroll_threshold(match.group("reroll")),
        )

    def roll(self, rng: random.Random | None = None) -> DiceRollResult:
        """Roll this expression and return a detailed result."""
        roller = rng or random.Random()
        rolls = tuple(self._roll_one(roller) for _ in range(self.count))
        kept = self._kept(rolls)
        return DiceRollResult(
            notation=self.notation,
            total=sum(kept) + self.modifier,
            rolls=rolls,
            kept=kept,
            modifier=self.modifier,
        )

    def minimum(self) -> int:
        """Return the minimum possible total."""
        return self._kept_count() + self.modifier

    def maximum(self) -> int | None:
        """Return the maximum possible total, or None when exploding is unbounded."""
        if self.explode:
            return None
        return self._kept_count() * self.sides + self.modifier

    def average(self) -> float:
        """Return the expected average total."""
        if self.explode or self.reroll_threshold is not None:
            return self._enumerated_average()
        if (
            self.keep_highest is None
            and self.keep_lowest is None
            and self.drop_highest is None
            and self.drop_lowest is None
        ):
            return self.count * (self.sides + 1) / 2 + self.modifier
        return self._enumerated_average()

    def _roll_one(self, rng: random.Random) -> int:
        total = rng.randint(1, self.sides)
        if self.reroll_threshold is not None and total <= self.reroll_threshold:
            total = rng.randint(1, self.sides)
        if self.explode:
            last = total
            guard = 0
            while last == self.sides:
                last = rng.randint(1, self.sides)
                total += last
                guard += 1
                if guard > 1000:
                    raise RuntimeError("exploding die exceeded safety limit")
        return total

    def _kept(self, rolls: tuple[int, ...]) -> tuple[int, ...]:
        if self.keep_highest is not None:
            return tuple(sorted(rolls, reverse=True)[: self.keep_highest])
        if self.keep_lowest is not None:
            return tuple(sorted(rolls)[: self.keep_lowest])
        if self.drop_highest is not None:
            return tuple(sorted(rolls)[: self.count - self.drop_highest])
        if self.drop_lowest is not None:
            return tuple(sorted(rolls, reverse=True)[: self.count - self.drop_lowest])
        return rolls

    def _kept_count(self) -> int:
        if self.keep_highest is not None:
            return self.keep_highest
        if self.keep_lowest is not None:
            return self.keep_lowest
        if self.drop_highest is not None:
            return self.count - self.drop_highest
        if self.drop_lowest is not None:
            return self.count - self.drop_lowest
        return self.count

    def _enumerated_average(self) -> float:
        if self.explode:
            if self.reroll_threshold is not None:
                raise ValueError("average for combined explode and reroll is not supported yet")
            base_average = self.sides * (self.sides + 1) / (2 * (self.sides - 1))
            return self._kept_count() * base_average + self.modifier
        outcomes = range(1, self.sides + 1)
        totals = []
        for rolls in product(outcomes, repeat=self.count):
            adjusted = tuple(
                self._rerolled_average_value(roll) if self.reroll_threshold is not None else roll
                for roll in rolls
            )
            totals.append(sum(self._kept(adjusted)))
        return sum(totals) / len(totals) + self.modifier

    def _rerolled_average_value(self, roll: int) -> float:
        if self.reroll_threshold is None or roll > self.reroll_threshold:
            return float(roll)
        return (self.sides + 1) / 2


def _parse_reroll_threshold(value: str | None) -> int | None:
    if value is None:
        return None
    threshold = value.removeprefix("r")
    for prefix in ("<=", "<", "="):
        threshold = threshold.removeprefix(prefix)
    if value.startswith(("r>", "r>=")):
        raise ValueError("only low reroll thresholds are supported")
    return int(threshold)
