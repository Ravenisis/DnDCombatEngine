"""Equipment models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from dnd_combat_engine.models.damage import DamageProfile


@dataclass(frozen=True, slots=True)
class Weapon:
    """A weapon with a typed damage profile."""

    name: str
    damage: DamageProfile
    properties: tuple[str, ...] = field(default_factory=tuple)
    range_normal: int | None = None
    range_long: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the weapon to plain JSON-compatible data."""
        return {
            "name": self.name,
            "damage": self.damage.to_dict(),
            "properties": list(self.properties),
            "range_normal": self.range_normal,
            "range_long": self.range_long,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a weapon from JSON-compatible data."""
        return cls(
            name=str(data["name"]),
            damage=DamageProfile.from_dict(data["damage"]),  # type: ignore[arg-type]
            properties=tuple(str(item) for item in data.get("properties", [])),
            range_normal=data.get("range_normal"),  # type: ignore[arg-type]
            range_long=data.get("range_long"),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class Armor:
    """Armor and shield defensive data."""

    name: str
    armor_class: int
    stealth_disadvantage: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize the armor to plain JSON-compatible data."""
        return {
            "name": self.name,
            "armor_class": self.armor_class,
            "stealth_disadvantage": self.stealth_disadvantage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build armor from JSON-compatible data."""
        return cls(
            name=str(data["name"]),
            armor_class=int(data["armor_class"]),
            stealth_disadvantage=bool(data.get("stealth_disadvantage", False)),
        )

