"""Feature engine orchestration."""

from __future__ import annotations

from collections.abc import Iterable

from dnd_combat_engine.engine.events import EngineEvent
from dnd_combat_engine.rules.features import Feature


class FeatureEngine:
    """Run feature plugins against events in deterministic order."""

    def __init__(self, features: Iterable[Feature] = ()) -> None:
        """Create a feature engine with ordered feature plugins."""
        self.features = tuple(features)

    def process(self, event: EngineEvent) -> EngineEvent:
        """Pass an event through every applicable feature."""
        current = event
        for feature in self.features:
            if feature.applies_to(current):
                current = feature.handle(current)
        return current

