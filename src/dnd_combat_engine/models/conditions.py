"""Condition models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class ConditionName(StrEnum):
    """Standard Dungeons & Dragons condition names."""

    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    EXHAUSTION = "exhaustion"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"


@dataclass(frozen=True, slots=True)
class Condition:
    """A condition applied to a character."""

    name: ConditionName
    source: str | None = None
    remaining_rounds: int | None = None

    def __post_init__(self) -> None:
        """Validate condition duration."""
        if self.remaining_rounds is not None and self.remaining_rounds < 1:
            raise ValueError("remaining rounds must be at least 1")

    def tick_round(self) -> Self | None:
        """Return the condition after one round, or None when it expires."""
        if self.remaining_rounds is None:
            return self
        if self.remaining_rounds == 1:
            return None
        return type(self)(
            name=self.name,
            source=self.source,
            remaining_rounds=self.remaining_rounds - 1,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the condition to plain JSON-compatible data."""
        return {
            "name": self.name.value,
            "source": self.source,
            "remaining_rounds": self.remaining_rounds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a condition from JSON-compatible data."""
        rounds = data.get("remaining_rounds")
        return cls(
            name=ConditionName(str(data["name"])),
            source=str(data["source"]) if data.get("source") is not None else None,
            remaining_rounds=int(rounds) if rounds is not None else None,
        )

