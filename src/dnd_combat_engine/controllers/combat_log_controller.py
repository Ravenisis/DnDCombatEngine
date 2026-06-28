"""Combat log controller workflows."""

from __future__ import annotations

from dataclasses import dataclass

from dnd_combat_engine.engine.attacks import AttackResult
from dnd_combat_engine.engine.initiative import InitiativeTracker
from dnd_combat_engine.models.combat_log import CombatLog, CombatLogEntry
from dnd_combat_engine.services.combat_log_service import CombatLogService


@dataclass(frozen=True, slots=True)
class CombatLogController:
    """UI-facing combat log workflow coordinator."""

    combat_log_service: CombatLogService

    def record_attack(self, log: CombatLog, result: AttackResult) -> CombatLog:
        """Record an attack result."""
        return self.combat_log_service.append_attack(log, result)

    def record_initiative(self, log: CombatLog, tracker: InitiativeTracker) -> CombatLog:
        """Record initiative order."""
        return self.combat_log_service.append_initiative(log, tracker)

    def latest(self, log: CombatLog, count: int = 10) -> tuple[CombatLogEntry, ...]:
        """Return the latest log entries."""
        return log.latest(count)

