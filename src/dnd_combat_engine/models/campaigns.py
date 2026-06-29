"""Campaign models."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Self


class CampaignStatus(StrEnum):
    """Lifecycle states for a campaign."""

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Campaign:
    """A campaign workspace that groups characters, encounters, and notes."""

    campaign_id: str
    name: str
    status: CampaignStatus = CampaignStatus.PLANNED
    character_ids: tuple[str, ...] = field(default_factory=tuple)
    encounter_ids: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate campaign identity and references."""
        if not self.campaign_id:
            raise ValueError("campaign_id is required")
        if not self.name:
            raise ValueError("name is required")
        if any(not character_id for character_id in self.character_ids):
            raise ValueError("character_ids cannot contain blank ids")
        if any(not encounter_id for encounter_id in self.encounter_ids):
            raise ValueError("encounter_ids cannot contain blank ids")
        if len(set(self.character_ids)) != len(self.character_ids):
            raise ValueError("character_ids cannot contain duplicates")
        if len(set(self.encounter_ids)) != len(self.encounter_ids):
            raise ValueError("encounter_ids cannot contain duplicates")

    def with_character(self, character_id: str) -> Self:
        """Return a campaign with a character reference added."""
        if not character_id:
            raise ValueError("character_id is required")
        if character_id in self.character_ids:
            return self
        return replace(self, character_ids=(*self.character_ids, character_id))

    def without_character(self, character_id: str) -> Self:
        """Return a campaign with a character reference removed."""
        return replace(
            self,
            character_ids=tuple(item for item in self.character_ids if item != character_id),
        )

    def with_encounter(self, encounter_id: str) -> Self:
        """Return a campaign with an encounter reference added."""
        if not encounter_id:
            raise ValueError("encounter_id is required")
        if encounter_id in self.encounter_ids:
            return self
        return replace(self, encounter_ids=(*self.encounter_ids, encounter_id))

    def without_encounter(self, encounter_id: str) -> Self:
        """Return a campaign with an encounter reference removed."""
        return replace(
            self,
            encounter_ids=tuple(item for item in self.encounter_ids if item != encounter_id),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the campaign to plain JSON-compatible data."""
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "status": self.status.value,
            "character_ids": list(self.character_ids),
            "encounter_ids": list(self.encounter_ids),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a campaign from JSON-compatible data."""
        return cls(
            campaign_id=str(data["campaign_id"]),
            name=str(data["name"]),
            status=CampaignStatus(str(data.get("status", CampaignStatus.PLANNED.value))),
            character_ids=tuple(str(item) for item in data.get("character_ids", [])),
            encounter_ids=tuple(str(item) for item in data.get("encounter_ids", [])),
            notes=str(data.get("notes", "")),
        )
