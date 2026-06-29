from dnd_combat_engine.controllers import CampaignController
from dnd_combat_engine.models import Campaign, CampaignStatus
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import CampaignService, PersistenceService


def test_campaign_controller_persists_and_updates_campaigns(tmp_path) -> None:
    controller = CampaignController(
        CampaignService(),
        PersistenceService(JsonFileStore(tmp_path)),
    )
    campaign = Campaign("starter", "Starter")

    updated = controller.activate(
        controller.add_encounter(
            controller.add_character(campaign, "vale"),
            "roadside_ambush",
        )
    )
    controller.save(updated)

    assert controller.list_ids() == ["starter"]
    assert controller.load("starter").status is CampaignStatus.ACTIVE
    assert controller.load("starter").character_ids == ("vale",)
