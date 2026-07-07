"""Encounter models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.monsters import Monster
from dnd_combat_engine.models.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_FIELD


class EncounterStatus(StrEnum):
    """Lifecycle states for an encounter."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class ParticipantKind(StrEnum):
    """Kinds of participants that can appear in an encounter."""

    CHARACTER = "character"
    MONSTER = "monster"


@dataclass(frozen=True, slots=True)
class EncounterParticipant:
    """A lightweight encounter participant reference."""

    participant_id: str
    name: str
    kind: ParticipantKind
    source_id: str
    quantity: int = 1
    initiative_bonus: int = 0
    current_hit_points: int | None = None

    def __post_init__(self) -> None:
        """Validate participant fields."""
        if not self.participant_id:
            raise ValueError("participant_id is required")
        if not self.name:
            raise ValueError("name is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.quantity < 1:
            raise ValueError("quantity must be at least 1")
        if self.current_hit_points is not None and self.current_hit_points < 0:
            raise ValueError("current_hit_points cannot be negative")

    @classmethod
    def from_character(cls, character: Character) -> Self:
        """Build an encounter participant from a character."""
        return cls(
            participant_id=character.character_id,
            name=character.name,
            kind=ParticipantKind.CHARACTER,
            source_id=character.character_id,
            initiative_bonus=character.abilities.modifier("dexterity"),
        )

    @classmethod
    def from_monster(cls, monster: Monster, quantity: int = 1) -> Self:
        """Build an encounter participant from a monster stat block."""
        return cls(
            participant_id=monster.monster_id,
            name=monster.name,
            kind=ParticipantKind.MONSTER,
            source_id=monster.monster_id,
            quantity=quantity,
            initiative_bonus=monster.abilities.modifier("dexterity"),
            current_hit_points=monster.hit_points.current * quantity,
        )

    def with_current_hit_points(self, current_hit_points: int) -> Self:
        """Return a copy with updated encounter-specific hit points."""
        return type(self)(
            participant_id=self.participant_id,
            name=self.name,
            kind=self.kind,
            source_id=self.source_id,
            quantity=self.quantity,
            initiative_bonus=self.initiative_bonus,
            current_hit_points=current_hit_points,
        )

    def apply_damage(self, amount: int, maximum_hit_points: int) -> tuple[Self, int]:
        """Return an updated participant and damage applied to current HP."""
        if amount < 0:
            raise ValueError("damage amount cannot be negative")
        current = maximum_hit_points if self.current_hit_points is None else self.current_hit_points
        dealt = min(amount, current)
        return self.with_current_hit_points(current - dealt), dealt

    def to_dict(self) -> dict[str, object]:
        """Serialize the participant to plain JSON-compatible data."""
        data: dict[str, object] = {
            "participant_id": self.participant_id,
            "name": self.name,
            "kind": self.kind.value,
            "source_id": self.source_id,
            "quantity": self.quantity,
            "initiative_bonus": self.initiative_bonus,
        }
        if self.current_hit_points is not None:
            data["current_hit_points"] = self.current_hit_points
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a participant from JSON-compatible data."""
        return cls(
            participant_id=str(data["participant_id"]),
            name=str(data["name"]),
            kind=ParticipantKind(str(data["kind"])),
            source_id=str(data["source_id"]),
            quantity=int(data.get("quantity", 1)),
            initiative_bonus=int(data.get("initiative_bonus", 0)),
            current_hit_points=(
                int(data["current_hit_points"])
                if data.get("current_hit_points") is not None
                else None
            ),
        )


@dataclass(frozen=True, slots=True)
class Encounter:
    """A planned or active encounter."""

    encounter_id: str
    name: str
    participants: tuple[EncounterParticipant, ...] = field(default_factory=tuple)
    status: EncounterStatus = EncounterStatus.DRAFT
    round_number: int = 1
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate encounter fields."""
        if not self.encounter_id:
            raise ValueError("encounter_id is required")
        if not self.name:
            raise ValueError("name is required")
        if self.round_number < 1:
            raise ValueError("round number must be at least 1")

    def with_participant(self, participant: EncounterParticipant) -> Self:
        """Return a copy with a participant added or replaced."""
        participants = tuple(
            current
            for current in self.participants
            if current.participant_id != participant.participant_id
        )
        return type(self)(
            encounter_id=self.encounter_id,
            name=self.name,
            participants=(*participants, participant),
            status=self.status,
            round_number=self.round_number,
            notes=self.notes,
        )

    def without_participant(self, participant_id: str) -> Self:
        """Return a copy without a participant."""
        return type(self)(
            encounter_id=self.encounter_id,
            name=self.name,
            participants=tuple(
                participant
                for participant in self.participants
                if participant.participant_id != participant_id
            ),
            status=self.status,
            round_number=self.round_number,
            notes=self.notes,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the encounter to plain JSON-compatible data."""
        return {
            SCHEMA_VERSION_FIELD: CURRENT_SCHEMA_VERSION,
            "encounter_id": self.encounter_id,
            "name": self.name,
            "participants": [participant.to_dict() for participant in self.participants],
            "status": self.status.value,
            "round_number": self.round_number,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build an encounter from JSON-compatible data."""
        return cls(
            encounter_id=str(data["encounter_id"]),
            name=str(data["name"]),
            participants=tuple(
                EncounterParticipant.from_dict(participant)
                for participant in data.get("participants", [])
            ),
            status=EncounterStatus(str(data.get("status", EncounterStatus.DRAFT.value))),
            round_number=int(data.get("round_number", 1)),
            notes=str(data.get("notes", "")),
        )
