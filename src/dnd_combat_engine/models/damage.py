"""Damage model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class DamageType(StrEnum):
    """Dungeons & Dragons damage types."""

    ACID = "acid"
    BLUDGEONING = "bludgeoning"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    PIERCING = "piercing"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    THUNDER = "thunder"


@dataclass(frozen=True, slots=True)
class DamageComponent:
    """One dice expression paired with one damage type."""

    dice: str
    damage_type: DamageType

    def to_dict(self) -> dict[str, str]:
        """Serialize the damage component to plain JSON-compatible data."""
        return {"dice": self.dice, "damage_type": self.damage_type.value}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        """Build a damage component from JSON-compatible data."""
        return cls(dice=data["dice"], damage_type=DamageType(data["damage_type"]))


@dataclass(frozen=True, slots=True)
class DamageProfile:
    """A collection of typed damage components."""

    components: tuple[DamageComponent, ...]

    def __post_init__(self) -> None:
        """Validate the profile has at least one component."""
        if not self.components:
            raise ValueError("damage profile must have at least one component")

    def add(self, component: DamageComponent) -> Self:
        """Return a new profile with an additional component."""
        return type(self)(components=(*self.components, component))

    def to_dict(self) -> list[dict[str, str]]:
        """Serialize the damage profile to plain JSON-compatible data."""
        return [component.to_dict() for component in self.components]

    @classmethod
    def from_dict(cls, data: list[dict[str, str]]) -> Self:
        """Build a damage profile from JSON-compatible data."""
        return cls(tuple(DamageComponent.from_dict(component) for component in data))

