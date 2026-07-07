"""Spell models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from dnd_combat_engine.models.damage import DamageProfile
from dnd_combat_engine.models.rules import RuleSource


class SpellSchool(StrEnum):
    """Dungeons & Dragons spell schools."""

    ABJURATION = "abjuration"
    CONJURATION = "conjuration"
    DIVINATION = "divination"
    ENCHANTMENT = "enchantment"
    EVOCATION = "evocation"
    ILLUSION = "illusion"
    NECROMANCY = "necromancy"
    TRANSMUTATION = "transmutation"


@dataclass(frozen=True, slots=True)
class Spell:
    """A spell definition independent of caster state."""

    spell_id: str
    name: str
    level: int
    school: SpellSchool
    casting_time: str
    range_text: str
    duration: str
    components: tuple[str, ...] = field(default_factory=tuple)
    concentration: bool = False
    ritual: bool = False
    damage: DamageProfile | None = None
    saving_throw: str | None = None
    description: str = ""
    rule_source: RuleSource | None = None

    def __post_init__(self) -> None:
        """Validate spell identity and level."""
        if not self.spell_id:
            raise ValueError("spell_id is required")
        if not self.name:
            raise ValueError("name is required")
        if not 0 <= self.level <= 9:
            raise ValueError("spell level must be between 0 and 9")
        if not self.casting_time:
            raise ValueError("casting time is required")
        if not self.range_text:
            raise ValueError("range is required")
        if not self.duration:
            raise ValueError("duration is required")

    @property
    def is_cantrip(self) -> bool:
        """Return whether this spell is a cantrip."""
        return self.level == 0

    def to_dict(self) -> dict[str, object]:
        """Serialize the spell to plain JSON-compatible data."""
        return {
            "spell_id": self.spell_id,
            "name": self.name,
            "level": self.level,
            "school": self.school.value,
            "casting_time": self.casting_time,
            "range_text": self.range_text,
            "duration": self.duration,
            "components": list(self.components),
            "concentration": self.concentration,
            "ritual": self.ritual,
            "damage": self.damage.to_dict() if self.damage else None,
            "saving_throw": self.saving_throw,
            "description": self.description,
            "rule_source": self.rule_source.to_dict() if self.rule_source else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a spell from JSON-compatible data."""
        damage_data = data.get("damage")
        return cls(
            spell_id=str(data["spell_id"]),
            name=str(data["name"]),
            level=int(data["level"]),
            school=SpellSchool(str(data["school"])),
            casting_time=str(data["casting_time"]),
            range_text=str(data["range_text"]),
            duration=str(data["duration"]),
            components=tuple(str(component) for component in data.get("components", [])),
            concentration=bool(data.get("concentration", False)),
            ritual=bool(data.get("ritual", False)),
            damage=DamageProfile.from_dict(damage_data) if isinstance(damage_data, list) else None,
            saving_throw=(
                str(data["saving_throw"]) if data.get("saving_throw") is not None else None
            ),
            description=str(data.get("description", "")),
            rule_source=_rule_source_from_data(data.get("rule_source")),
        )


def _rule_source_from_data(data: object) -> RuleSource | None:
    if isinstance(data, dict):
        return RuleSource.from_dict(data)
    return None
