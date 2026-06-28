"""Initiative business operations."""

from __future__ import annotations

import random
from collections.abc import Iterable

from dnd_combat_engine.engine.initiative import InitiativeEntry, InitiativeTracker
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.services.dice_service import DiceService


class InitiativeService:
    """Roll and manage initiative order for encounters."""

    def __init__(self, dice_service: DiceService | None = None) -> None:
        """Create the service with an optional dice dependency."""
        self.dice_service = dice_service or DiceService()

    def roll_initiative(
        self,
        combatants: Iterable[Character],
        rng: random.Random | None = None,
    ) -> InitiativeTracker:
        """Roll initiative for combatants and return a sorted tracker."""
        entries = tuple(self._roll_entry(combatant, rng=rng) for combatant in combatants)
        if not entries:
            raise ValueError("at least one combatant is required")
        return InitiativeTracker(tuple(sorted(entries, key=_initiative_sort_key)))

    def _roll_entry(self, combatant: Character, rng: random.Random | None) -> InitiativeEntry:
        roll = self.dice_service.roll("1d20", rng=rng)
        dexterity_modifier = combatant.abilities.modifier("dexterity")
        return InitiativeEntry(
            combatant=combatant,
            roll=roll,
            dexterity_modifier=dexterity_modifier,
            total=roll.total + dexterity_modifier,
        )


def _initiative_sort_key(entry: InitiativeEntry) -> tuple[int, int, str, str]:
    return (
        -entry.total,
        -entry.dexterity_modifier,
        entry.combatant.name.lower(),
        entry.combatant.character_id,
    )

