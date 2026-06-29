import pytest

from dnd_combat_engine.models import Campaign, CampaignStatus
from dnd_combat_engine.services import CampaignService


def test_campaign_service_manages_references_and_status() -> None:
    service = CampaignService()
    campaign = Campaign("starter", "Starter")

    campaign = service.add_character(campaign, "vale")
    campaign = service.add_encounter(campaign, "roadside_ambush")
    active = service.activate(campaign)
    completed = service.complete(active)
    archived = service.archive(completed)

    assert active.status is CampaignStatus.ACTIVE
    assert completed.status is CampaignStatus.COMPLETED
    assert archived.status is CampaignStatus.ARCHIVED
    assert service.remove_character(campaign, "vale").character_ids == ()
    assert service.remove_encounter(campaign, "roadside_ambush").encounter_ids == ()


def test_campaign_service_rejects_archived_campaign_changes() -> None:
    service = CampaignService()
    archived = Campaign("starter", "Starter", status=CampaignStatus.ARCHIVED)

    with pytest.raises(ValueError):
        service.add_character(archived, "vale")
    with pytest.raises(ValueError):
        service.add_encounter(archived, "roadside_ambush")
    with pytest.raises(ValueError):
        service.activate(archived)
    with pytest.raises(ValueError):
        service.complete(archived)
