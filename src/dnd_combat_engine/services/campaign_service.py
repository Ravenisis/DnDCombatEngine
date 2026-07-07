"""Campaign business operations."""

from __future__ import annotations

from dnd_combat_engine.models.campaigns import Campaign, CampaignStatus


class CampaignService:
    """Manage campaign lifecycle and references."""

    def add_character(self, campaign: Campaign, character_id: str) -> Campaign:
        """Return a campaign with a character reference added."""
        self._ensure_editable(campaign)
        return campaign.with_character(character_id)

    def remove_character(self, campaign: Campaign, character_id: str) -> Campaign:
        """Return a campaign with a character reference removed."""
        self._ensure_editable(campaign)
        return campaign.without_character(character_id)

    def add_encounter(self, campaign: Campaign, encounter_id: str) -> Campaign:
        """Return a campaign with an encounter reference added."""
        self._ensure_editable(campaign)
        return campaign.with_encounter(encounter_id)

    def remove_encounter(self, campaign: Campaign, encounter_id: str) -> Campaign:
        """Return a campaign with an encounter reference removed."""
        self._ensure_editable(campaign)
        return campaign.without_encounter(encounter_id)

    def activate(self, campaign: Campaign) -> Campaign:
        """Return an active campaign."""
        if campaign.status is CampaignStatus.ARCHIVED:
            raise ValueError("archived campaigns cannot be activated")
        return self._with_status(campaign, CampaignStatus.ACTIVE)

    def complete(self, campaign: Campaign) -> Campaign:
        """Return a completed campaign."""
        if campaign.status is CampaignStatus.ARCHIVED:
            raise ValueError("archived campaigns cannot be completed")
        return self._with_status(campaign, CampaignStatus.COMPLETED)

    def archive(self, campaign: Campaign) -> Campaign:
        """Return an archived campaign."""
        return self._with_status(campaign, CampaignStatus.ARCHIVED)

    def _ensure_editable(self, campaign: Campaign) -> None:
        if campaign.status is CampaignStatus.ARCHIVED:
            raise ValueError("archived campaigns cannot be edited")

    def _with_status(self, campaign: Campaign, status: CampaignStatus) -> Campaign:
        return Campaign(
            campaign_id=campaign.campaign_id,
            name=campaign.name,
            status=status,
            character_ids=campaign.character_ids,
            encounter_ids=campaign.encounter_ids,
            notes=campaign.notes,
            activity_log=campaign.activity_log,
        )
