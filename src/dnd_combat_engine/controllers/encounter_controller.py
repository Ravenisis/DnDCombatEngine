"""Encounter controller workflows."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dnd_combat_engine.engine.initiative import InitiativeTracker
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.encounters import Encounter, EncounterParticipant
from dnd_combat_engine.models.monsters import Monster
from dnd_combat_engine.services.encounter_service import EncounterService
from dnd_combat_engine.services.initiative_service import InitiativeService
from dnd_combat_engine.services.persistence_service import PersistenceService


@dataclass(frozen=True, slots=True)
class EncounterController:
    """UI-facing encounter workflow coordinator."""

    encounter_service: EncounterService
    initiative_service: InitiativeService
    persistence_service: PersistenceService

    def load(self, encounter_id: str) -> Encounter:
        """Load an encounter by id."""
        return self.persistence_service.load_encounter(encounter_id)

    def save(self, encounter: Encounter) -> None:
        """Save an encounter."""
        self.persistence_service.save_encounter(encounter)

    def add_character(self, encounter: Encounter, character: Character) -> Encounter:
        """Return an encounter with a character participant."""
        return self.encounter_service.add_participant(
            encounter,
            EncounterParticipant.from_character(character),
        )

    def add_monster(self, encounter: Encounter, monster: Monster, quantity: int = 1) -> Encounter:
        """Return an encounter with a monster participant."""
        return self.encounter_service.add_participant(
            encounter,
            EncounterParticipant.from_monster(monster, quantity=quantity),
        )

    def start_and_roll_initiative(
        self,
        encounter: Encounter,
        combatants: tuple[Character, ...],
        rng: random.Random | None = None,
    ) -> tuple[Encounter, InitiativeTracker]:
        """Start an encounter and roll initiative for concrete combatants."""
        active = self.encounter_service.start(encounter)
        tracker = self.initiative_service.roll_initiative(combatants, rng=rng)
        return active, tracker

