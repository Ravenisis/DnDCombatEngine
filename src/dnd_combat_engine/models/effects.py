"""Targeting and effect resolution models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class TargetKind(StrEnum):
    """Kinds of combat targets the GUI can select."""

    CHARACTER = "character"
    MONSTER = "monster"


class EffectKind(StrEnum):
    """High-level effect categories resolved by action controls."""

    ATTACK = "attack"
    BUFF = "buff"
    CONDITION = "condition"
    DAMAGE = "damage"
    HEALING = "healing"
    RESOURCE = "resource"
    SAVE = "save"
    UTILITY = "utility"


@dataclass(frozen=True, slots=True)
class TargetReference:
    """A selected target reference independent of storage details."""

    target_id: str
    name: str
    kind: TargetKind
    source_id: str

    def __post_init__(self) -> None:
        """Validate target reference fields."""
        if not self.target_id:
            raise ValueError("target_id is required")
        if not self.name:
            raise ValueError("name is required")
        if not self.source_id:
            raise ValueError("source_id is required")

    def to_dict(self) -> dict[str, str]:
        """Serialize the target reference to plain JSON-compatible data."""
        return {
            "target_id": self.target_id,
            "name": self.name,
            "kind": self.kind.value,
            "source_id": self.source_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a target reference from JSON-compatible data."""
        return cls(
            target_id=str(data["target_id"]),
            name=str(data["name"]),
            kind=TargetKind(str(data["kind"])),
            source_id=str(data["source_id"]),
        )


@dataclass(frozen=True, slots=True)
class EffectResolution:
    """A resolved effect summary for combat workspace logging."""

    source_name: str
    effect_name: str
    effect_kind: EffectKind
    target: TargetReference | None = None
    total: int | None = None
    detail: str = ""

    def message(self) -> str:
        """Return a compact player-facing resolution message."""
        target_text = f" on {self.target.name}" if self.target is not None else ""
        total_text = "" if self.total is None else f" Total {self.total}."
        detail_text = "" if not self.detail else f" {self.detail}"
        return (
            f"{self.source_name} resolves {self.effect_name}"
            f"{target_text} [{self.effect_kind.value}].{total_text}{detail_text}"
        )
