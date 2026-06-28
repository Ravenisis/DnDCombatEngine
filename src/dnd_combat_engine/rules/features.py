"""Feature plugin protocol."""

from __future__ import annotations

from typing import Protocol

from dnd_combat_engine.engine.events import EngineEvent


class Feature(Protocol):
    """Common interface for future class, spell, feat, and condition features."""

    name: str

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should inspect or modify an event."""

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Return the event after this feature has handled it."""

