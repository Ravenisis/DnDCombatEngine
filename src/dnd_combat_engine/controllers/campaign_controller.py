"""Campaign controller workflows."""

from __future__ import annotations

from dataclasses import dataclass

from dnd_combat_engine.models.campaigns import Campaign
from dnd_combat_engine.services.campaign_service import CampaignService
from dnd_combat_engine.services.persistence_service import PersistenceService


@dataclass(frozen=True, slots=True)
class CampaignController:
    """UI-facing campaign workflow coordinator."""

    campaign_service: CampaignService
    persistence_service: PersistenceService

    def load(self, campaign_id: str) -> Campaign:
        """Load a campaign by id."""
        return self.persistence_service.load_campaign(campaign_id)

    def save(self, campaign: Campaign) -> None:
        """Save a campaign."""
        self.persistence_service.save_campaign(campaign)

    def list_ids(self) -> list[str]:
        """List saved campaign ids."""
        return self.persistence_service.list_campaign_ids()

    def add_character(self, campaign: Campaign, character_id: str) -> Campaign:
        """Return a campaign with a character reference added."""
        return self.campaign_service.add_character(campaign, character_id)

    def add_encounter(self, campaign: Campaign, encounter_id: str) -> Campaign:
        """Return a campaign with an encounter reference added."""
        return self.campaign_service.add_encounter(campaign, encounter_id)

    def activate(self, campaign: Campaign) -> Campaign:
        """Return an active campaign."""
        return self.campaign_service.activate(campaign)
