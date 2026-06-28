"""Initiative and turn order primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.utils.dice import DiceRollResult


@dataclass(frozen=True, slots=True)
class InitiativeEntry:
    """One combatant's position in initiative order."""

    combatant: Character
    roll: DiceRollResult
    dexterity_modifier: int
    total: int


@dataclass(frozen=True, slots=True)
class InitiativeTracker:
    """Immutable turn-order state for an encounter."""

    entries: tuple[InitiativeEntry, ...]
    active_index: int = 0
    round_number: int = 1

    def __post_init__(self) -> None:
        """Validate turn-order bounds."""
        if self.round_number < 1:
            raise ValueError("round number must be at least 1")
        if self.entries and not 0 <= self.active_index < len(self.entries):
            raise ValueError("active index is outside the initiative order")
        if not self.entries and self.active_index != 0:
            raise ValueError("empty initiative trackers must use active index 0")

    @property
    def current(self) -> InitiativeEntry | None:
        """Return the current initiative entry, if any."""
        if not self.entries:
            return None
        return self.entries[self.active_index]

    @property
    def ordered_combatants(self) -> tuple[Character, ...]:
        """Return combatants in initiative order."""
        return tuple(entry.combatant for entry in self.entries)

    def advance(self) -> Self:
        """Advance to the next turn and increment the round on wrap."""
        if not self.entries:
            return self
        next_index = (self.active_index + 1) % len(self.entries)
        next_round = self.round_number + 1 if next_index == 0 else self.round_number
        return type(self)(self.entries, active_index=next_index, round_number=next_round)

    def remove(self, character_id: str) -> Self:
        """Return a tracker without a combatant."""
        remaining = tuple(
            entry for entry in self.entries if entry.combatant.character_id != character_id
        )
        if len(remaining) == len(self.entries):
            return self
        if not remaining:
            return type(self)((), active_index=0, round_number=self.round_number)

        removed_before_active = any(
            entry.combatant.character_id == character_id
            for entry in self.entries[: self.active_index]
        )
        active_index = self.active_index - 1 if removed_before_active else self.active_index
        active_index = min(active_index, len(remaining) - 1)
        return type(self)(remaining, active_index=active_index, round_number=self.round_number)

