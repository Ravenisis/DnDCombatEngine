import pytest

from dnd_combat_engine.models import Campaign, CampaignStatus


def test_campaign_round_trips_to_plain_data() -> None:
    campaign = Campaign(
        campaign_id="starter",
        name="Starter",
        status=CampaignStatus.ACTIVE,
        character_ids=("vale",),
        encounter_ids=("roadside_ambush",),
        notes="Opening road encounter.",
    )

    restored = Campaign.from_dict(campaign.to_dict())

    assert restored == campaign


def test_campaign_adds_and_removes_references_without_duplicates() -> None:
    campaign = Campaign("starter", "Starter")

    updated = campaign.with_character("vale").with_character("vale").with_encounter("ambush")

    assert updated.character_ids == ("vale",)
    assert updated.encounter_ids == ("ambush",)
    assert updated.without_character("vale").character_ids == ()
    assert updated.without_character("missing").character_ids == ("vale",)
    assert updated.without_encounter("ambush").encounter_ids == ()
    assert updated.without_encounter("missing").encounter_ids == ("ambush",)


def test_campaign_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        Campaign("", "Starter")
    with pytest.raises(ValueError):
        Campaign("starter", "")
    with pytest.raises(ValueError):
        Campaign("starter", "Starter", character_ids=("",))
    with pytest.raises(ValueError):
        Campaign("starter", "Starter", encounter_ids=("",))
    with pytest.raises(ValueError):
        Campaign("starter", "Starter", character_ids=("vale", "vale"))
    with pytest.raises(ValueError):
        Campaign("starter", "Starter", encounter_ids=("ambush", "ambush"))
    with pytest.raises(ValueError):
        Campaign("starter", "Starter").with_character("")
    with pytest.raises(ValueError):
        Campaign("starter", "Starter").with_encounter("")
