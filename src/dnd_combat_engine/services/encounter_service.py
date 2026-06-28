"""Encounter business operations."""

from __future__ import annotations

from dnd_combat_engine.models.encounters import (
    Encounter,
    EncounterParticipant,
    EncounterStatus,
    ParticipantKind,
)


class EncounterService:
    """Manage encounter lifecycle and participants."""

    def add_participant(
        self,
        encounter: Encounter,
        participant: EncounterParticipant,
    ) -> Encounter:
        """Return an encounter with a participant added or replaced."""
        if encounter.status is EncounterStatus.COMPLETED:
            raise ValueError("cannot add participants to a completed encounter")
        return encounter.with_participant(participant)

    def remove_participant(self, encounter: Encounter, participant_id: str) -> Encounter:
        """Return an encounter without a participant."""
        if encounter.status is EncounterStatus.COMPLETED:
            raise ValueError("cannot remove participants from a completed encounter")
        return encounter.without_participant(participant_id)

    def start(self, encounter: Encounter) -> Encounter:
        """Start an encounter that has at least one participant."""
        if not encounter.participants:
            raise ValueError("cannot start an encounter without participants")
        return Encounter(
            encounter_id=encounter.encounter_id,
            name=encounter.name,
            participants=encounter.participants,
            status=EncounterStatus.ACTIVE,
            round_number=1,
            notes=encounter.notes,
        )

    def advance_round(self, encounter: Encounter) -> Encounter:
        """Advance an active encounter by one round."""
        if encounter.status is not EncounterStatus.ACTIVE:
            raise ValueError("only active encounters can advance rounds")
        return Encounter(
            encounter_id=encounter.encounter_id,
            name=encounter.name,
            participants=encounter.participants,
            status=encounter.status,
            round_number=encounter.round_number + 1,
            notes=encounter.notes,
        )

    def complete(self, encounter: Encounter) -> Encounter:
        """Mark an encounter as completed."""
        return Encounter(
            encounter_id=encounter.encounter_id,
            name=encounter.name,
            participants=encounter.participants,
            status=EncounterStatus.COMPLETED,
            round_number=encounter.round_number,
            notes=encounter.notes,
        )

    def total_monsters(self, encounter: Encounter) -> int:
        """Return the total monster count in an encounter."""
        return sum(
            participant.quantity
            for participant in encounter.participants
            if participant.kind is ParticipantKind.MONSTER
        )

