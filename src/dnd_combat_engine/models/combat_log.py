"""Combat log models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import uuid4


class CombatLogEntryType(StrEnum):
    """Kinds of combat log entries."""

    ATTACK = "attack"
    DAMAGE = "damage"
    HEALING = "healing"
    INITIATIVE = "initiative"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class CombatLogEntry:
    """A single combat log entry."""

    message: str
    entry_type: CombatLogEntryType = CombatLogEntryType.SYSTEM
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate log entry content."""
        if not self.message:
            raise ValueError("combat log message is required")

    def to_dict(self) -> dict[str, object]:
        """Serialize the log entry to plain JSON-compatible data."""
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type.value,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a log entry from JSON-compatible data."""
        return cls(
            entry_id=str(data["entry_id"]),
            entry_type=CombatLogEntryType(str(data["entry_type"])),
            message=str(data["message"]),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            metadata=data.get("metadata", {}),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class CombatLog:
    """An ordered combat log."""

    entries: tuple[CombatLogEntry, ...] = field(default_factory=tuple)

    def append(self, entry: CombatLogEntry) -> Self:
        """Return a new combat log with an entry appended."""
        return type(self)((*self.entries, entry))

    def latest(self, count: int) -> tuple[CombatLogEntry, ...]:
        """Return the most recent log entries."""
        if count < 1:
            raise ValueError("count must be at least 1")
        return self.entries[-count:]

    def to_dict(self) -> dict[str, object]:
        """Serialize the log to plain JSON-compatible data."""
        return {"entries": [entry.to_dict() for entry in self.entries]}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a combat log from JSON-compatible data."""
        return cls(
            tuple(CombatLogEntry.from_dict(entry) for entry in data.get("entries", []))
        )

