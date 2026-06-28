"""Event primitives for future combat and rules processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class EngineEvent:
    """Base event passed between the combat engine and feature engine."""

    name: str
    payload: dict[str, object] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AttackStartedEvent(EngineEvent):
    """Event emitted when an attack workflow begins."""

    def __init__(self, payload: dict[str, object] | None = None) -> None:
        """Create an attack-started event with an optional payload."""
        EngineEvent.__init__(self, name="attack.started", payload=payload or {})


class AttackFinishedEvent(EngineEvent):
    """Event emitted when an attack workflow finishes."""

    def __init__(self, payload: dict[str, object] | None = None) -> None:
        """Create an attack-finished event with an optional payload."""
        EngineEvent.__init__(self, name="attack.finished", payload=payload or {})
