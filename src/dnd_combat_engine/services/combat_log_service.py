"""Combat log business operations."""

from __future__ import annotations

from dnd_combat_engine.engine.attacks import AttackResult
from dnd_combat_engine.engine.initiative import InitiativeTracker
from dnd_combat_engine.models.combat_log import CombatLog, CombatLogEntry, CombatLogEntryType


class CombatLogService:
    """Build combat log entries from engine results."""

    def append_attack(self, log: CombatLog, result: AttackResult) -> CombatLog:
        """Append a readable attack result entry."""
        attacker = result.request.attacker.name
        target = result.request.target.name
        outcome = "critically hits" if result.critical else "hits" if result.hit else "misses"
        message = f"{attacker} {outcome} {target} with {result.request.weapon.name}."
        if result.hit:
            message += f" Damage: {result.damage_total}."
        return log.append(
            CombatLogEntry(
                message=message,
                entry_type=CombatLogEntryType.ATTACK,
                metadata={
                    "attack_total": result.attack_total,
                    "damage_total": result.damage_total,
                    "hit": result.hit,
                    "critical": result.critical,
                },
            )
        )

    def append_initiative(self, log: CombatLog, tracker: InitiativeTracker) -> CombatLog:
        """Append an initiative order entry."""
        order = ", ".join(entry.combatant.name for entry in tracker.entries)
        return log.append(
            CombatLogEntry(
                message=f"Initiative order: {order}.",
                entry_type=CombatLogEntryType.INITIATIVE,
                metadata={"round_number": tracker.round_number},
            )
        )

