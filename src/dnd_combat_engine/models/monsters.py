"""Monster models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction
from typing import Self

from dnd_combat_engine.models.abilities import AbilityScores
from dnd_combat_engine.models.damage import DamageType
from dnd_combat_engine.models.equipment import Weapon
from dnd_combat_engine.models.hit_points import HitPoints
from dnd_combat_engine.models.rules import RuleSource
from dnd_combat_engine.models.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_FIELD


class CreatureSize(StrEnum):
    """Dungeons & Dragons creature sizes."""

    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    GARGANTUAN = "gargantuan"


class CreatureType(StrEnum):
    """Dungeons & Dragons creature types."""

    ABERRATION = "aberration"
    BEAST = "beast"
    CELESTIAL = "celestial"
    CONSTRUCT = "construct"
    DRAGON = "dragon"
    ELEMENTAL = "elemental"
    FEY = "fey"
    FIEND = "fiend"
    GIANT = "giant"
    HUMANOID = "humanoid"
    MONSTROSITY = "monstrosity"
    OOZE = "ooze"
    PLANT = "plant"
    UNDEAD = "undead"


@dataclass(frozen=True, slots=True)
class Monster:
    """A monster stat block model independent of combat workflow."""

    monster_id: str
    name: str
    armor_class: int
    hit_points: HitPoints
    abilities: AbilityScores
    challenge_rating: Fraction
    size: CreatureSize = CreatureSize.MEDIUM
    creature_type: CreatureType = CreatureType.HUMANOID
    speed: dict[str, int] = field(default_factory=lambda: {"walk": 30})
    actions: tuple[Weapon, ...] = field(default_factory=tuple)
    senses: tuple[str, ...] = field(default_factory=tuple)
    languages: tuple[str, ...] = field(default_factory=tuple)
    damage_resistances: tuple[DamageType, ...] = field(default_factory=tuple)
    damage_immunities: tuple[DamageType, ...] = field(default_factory=tuple)
    condition_immunities: tuple[str, ...] = field(default_factory=tuple)
    rule_source: RuleSource | None = None

    def __post_init__(self) -> None:
        """Validate monster identity and stat block values."""
        if not self.monster_id:
            raise ValueError("monster_id is required")
        if not self.name:
            raise ValueError("name is required")
        if self.armor_class < 1:
            raise ValueError("armor class must be at least 1")
        if self.challenge_rating < 0:
            raise ValueError("challenge rating cannot be negative")
        if any(value < 0 for value in self.speed.values()):
            raise ValueError("speed values cannot be negative")

    def to_dict(self) -> dict[str, object]:
        """Serialize the monster to plain JSON-compatible data."""
        return {
            SCHEMA_VERSION_FIELD: CURRENT_SCHEMA_VERSION,
            "monster_id": self.monster_id,
            "name": self.name,
            "armor_class": self.armor_class,
            "hit_points": self.hit_points.to_dict(),
            "abilities": self.abilities.to_dict(),
            "challenge_rating": _format_fraction(self.challenge_rating),
            "size": self.size.value,
            "creature_type": self.creature_type.value,
            "speed": self.speed,
            "actions": [action.to_dict() for action in self.actions],
            "senses": list(self.senses),
            "languages": list(self.languages),
            "damage_resistances": [damage_type.value for damage_type in self.damage_resistances],
            "damage_immunities": [damage_type.value for damage_type in self.damage_immunities],
            "condition_immunities": list(self.condition_immunities),
            "rule_source": self.rule_source.to_dict() if self.rule_source else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a monster from JSON-compatible data."""
        return cls(
            monster_id=str(data["monster_id"]),
            name=str(data["name"]),
            armor_class=int(data["armor_class"]),
            hit_points=HitPoints.from_dict(data["hit_points"]),  # type: ignore[arg-type]
            abilities=AbilityScores.from_dict(data["abilities"]),  # type: ignore[arg-type]
            challenge_rating=_parse_fraction(data["challenge_rating"]),
            size=CreatureSize(str(data.get("size", CreatureSize.MEDIUM.value))),
            creature_type=CreatureType(str(data.get("creature_type", CreatureType.HUMANOID.value))),
            speed={str(key): int(value) for key, value in data.get("speed", {}).items()},
            actions=tuple(Weapon.from_dict(action) for action in data.get("actions", [])),
            senses=tuple(str(sense) for sense in data.get("senses", [])),
            languages=tuple(str(language) for language in data.get("languages", [])),
            damage_resistances=tuple(
                DamageType(str(damage_type)) for damage_type in data.get("damage_resistances", [])
            ),
            damage_immunities=tuple(
                DamageType(str(damage_type)) for damage_type in data.get("damage_immunities", [])
            ),
            condition_immunities=tuple(
                str(condition) for condition in data.get("condition_immunities", [])
            ),
            rule_source=_rule_source_from_data(data.get("rule_source")),
        )


def _format_fraction(value: Fraction) -> str | int:
    if value.denominator == 1:
        return value.numerator
    return f"{value.numerator}/{value.denominator}"


def _parse_fraction(value: object) -> Fraction:
    return Fraction(str(value))


def _rule_source_from_data(data: object) -> RuleSource | None:
    if isinstance(data, dict):
        return RuleSource.from_dict(data)
    return None
