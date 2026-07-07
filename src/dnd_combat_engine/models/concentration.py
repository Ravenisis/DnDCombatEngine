"""Concentration state models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from dnd_combat_engine.models.effects import TargetReference
from dnd_combat_engine.models.rules import RuleSource


class ConcentrationOutcome(StrEnum):
    """Possible concentration lifecycle outcomes."""

    STARTED = "started"
    REPLACED = "replaced"
    MAINTAINED = "maintained"
    BROKEN = "broken"


@dataclass(frozen=True, slots=True)
class ConcentrationState:
    """An active concentration effect and the targets depending on it."""

    caster_id: str
    effect_id: str
    effect_name: str
    targets: tuple[TargetReference, ...] = field(default_factory=tuple)
    duration_text: str = ""
    rule_source: RuleSource | None = None

    def __post_init__(self) -> None:
        """Validate concentration identity fields."""
        if not self.caster_id:
            raise ValueError("caster_id is required")
        if not self.effect_id:
            raise ValueError("effect_id is required")
        if not self.effect_name:
            raise ValueError("effect_name is required")

    def to_dict(self) -> dict[str, object]:
        """Serialize concentration state to JSON-compatible data."""
        return {
            "caster_id": self.caster_id,
            "effect_id": self.effect_id,
            "effect_name": self.effect_name,
            "targets": [target.to_dict() for target in self.targets],
            "duration_text": self.duration_text,
            "rule_source": self.rule_source.to_dict() if self.rule_source else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build concentration state from JSON-compatible data."""
        return cls(
            caster_id=str(data["caster_id"]),
            effect_id=str(data["effect_id"]),
            effect_name=str(data["effect_name"]),
            targets=tuple(
                TargetReference.from_dict(target)
                for target in data.get("targets", [])
                if isinstance(target, dict)
            ),
            duration_text=str(data.get("duration_text", "")),
            rule_source=_rule_source_from_data(data.get("rule_source")),
        )


@dataclass(frozen=True, slots=True)
class ConcentrationResult:
    """A player-facing concentration lifecycle result."""

    outcome: ConcentrationOutcome
    state: ConcentrationState | None = None
    previous: ConcentrationState | None = None
    save_dc: int | None = None
    save_total: int | None = None

    def message(self) -> str:
        """Return a compact log message for the concentration result."""
        if self.outcome == ConcentrationOutcome.STARTED and self.state is not None:
            return f"{self.state.caster_id} starts concentrating on {self.state.effect_name}."
        if self.outcome == ConcentrationOutcome.REPLACED and self.state is not None:
            previous_name = (
                self.previous.effect_name if self.previous is not None else "another effect"
            )
            return (
                f"{self.state.caster_id} stops concentrating on {previous_name} "
                f"and starts concentrating on {self.state.effect_name}."
            )
        if self.outcome == ConcentrationOutcome.MAINTAINED and self.state is not None:
            return (
                f"{self.state.caster_id} maintains concentration on {self.state.effect_name} "
                f"(DC {self.save_dc}, total {self.save_total})."
            )
        if self.previous is not None:
            return f"{self.previous.caster_id} loses concentration on {self.previous.effect_name}."
        return "Concentration ends."


def concentration_save_dc(damage_taken: int) -> int:
    """Return the Constitution save DC to maintain concentration after damage."""
    if damage_taken < 0:
        raise ValueError("damage taken cannot be negative")
    return max(10, damage_taken // 2)


def _rule_source_from_data(data: object) -> RuleSource | None:
    if isinstance(data, dict):
        return RuleSource.from_dict(data)
    return None
