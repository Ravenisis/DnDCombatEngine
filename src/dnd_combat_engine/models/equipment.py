"""Equipment models."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from dnd_combat_engine.models.damage import DamageComponent, DamageProfile
from dnd_combat_engine.models.rules import RuleSource


class EquipmentSlot(StrEnum):
    """Wearable and wielded locations on a character."""

    HEAD = "head"
    NECK = "neck"
    BACK = "back"
    CHEST = "chest"
    HANDS = "hands"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    WAIST = "waist"
    LEGS = "legs"
    FEET = "feet"
    RING_LEFT = "ring_left"
    RING_RIGHT = "ring_right"


@dataclass(frozen=True, slots=True)
class Weapon:
    """A weapon with a typed damage profile."""

    name: str
    damage: DamageProfile
    versatile_damage: DamageProfile | None = None
    properties: tuple[str, ...] = field(default_factory=tuple)
    range_normal: int | None = None
    range_long: int | None = None
    rule_source: RuleSource | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the weapon to plain JSON-compatible data."""
        return {
            "name": self.name,
            "damage": self.damage.to_dict(),
            "versatile_damage": (
                self.versatile_damage.to_dict() if self.versatile_damage else None
            ),
            "properties": list(self.properties),
            "range_normal": self.range_normal,
            "range_long": self.range_long,
            "rule_source": self.rule_source.to_dict() if self.rule_source else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a weapon from JSON-compatible data."""
        damage = DamageProfile.from_dict(data["damage"])  # type: ignore[arg-type]
        properties = tuple(str(item) for item in data.get("properties", []))
        versatile_data = data.get("versatile_damage")
        return cls(
            name=str(data["name"]),
            damage=damage,
            versatile_damage=(
                DamageProfile.from_dict(versatile_data)  # type: ignore[arg-type]
                if isinstance(versatile_data, list)
                else _infer_versatile_damage(str(data["name"]), damage, properties)
            ),
            properties=properties,
            range_normal=data.get("range_normal"),  # type: ignore[arg-type]
            range_long=data.get("range_long"),  # type: ignore[arg-type]
            rule_source=_rule_source_from_data(data.get("rule_source")),
        )


def _infer_versatile_damage(
    name: str,
    damage: DamageProfile,
    properties: tuple[str, ...],
) -> DamageProfile | None:
    if not any("versatile" in value.casefold() for value in properties):
        return None
    versatile_die = {
        "battleaxe": "1d10",
        "longsword": "1d10",
        "quarterstaff": "1d8",
        "spear": "1d8",
        "trident": "1d10",
        "warhammer": "1d10",
    }.get(name.casefold())
    if versatile_die is None or len(damage.components) != 1:
        return None
    component = damage.components[0]
    modifier = re.search(r"([+-]\d+)$", component.dice)
    dice = f"{versatile_die}{modifier.group(1) if modifier else ''}"
    return DamageProfile((DamageComponent(dice, component.damage_type),))


@dataclass(frozen=True, slots=True)
class Armor:
    """Armor and shield defensive data."""

    name: str
    armor_class: int
    stealth_disadvantage: bool = False
    rule_source: RuleSource | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the armor to plain JSON-compatible data."""
        return {
            "name": self.name,
            "armor_class": self.armor_class,
            "stealth_disadvantage": self.stealth_disadvantage,
            "rule_source": self.rule_source.to_dict() if self.rule_source else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build armor from JSON-compatible data."""
        return cls(
            name=str(data["name"]),
            armor_class=int(data["armor_class"]),
            stealth_disadvantage=bool(data.get("stealth_disadvantage", False)),
            rule_source=_rule_source_from_data(data.get("rule_source")),
        )


def _rule_source_from_data(data: object) -> RuleSource | None:
    if isinstance(data, dict):
        return RuleSource.from_dict(data)
    return None
