"""Ability score model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Self

AbilityName = Literal[
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
]


@dataclass(frozen=True, slots=True)
class AbilityScores:
    """The six Dungeons & Dragons ability scores."""

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def __post_init__(self) -> None:
        """Validate ability scores."""
        for name, value in asdict(self).items():
            if value < 1:
                raise ValueError(f"{name} must be at least 1")

    def modifier(self, ability: AbilityName) -> int:
        """Return the D&D modifier for an ability."""
        score = getattr(self, ability)
        return (score - 10) // 2

    def to_dict(self) -> dict[str, int]:
        """Serialize the ability scores to plain JSON-compatible data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> Self:
        """Build ability scores from JSON-compatible data."""
        return cls(**data)

