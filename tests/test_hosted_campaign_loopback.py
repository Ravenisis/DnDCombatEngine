"""Loopback smoke coverage for the local hosted-campaign backend."""

from pathlib import Path

from dnd_combat_engine.app import create_app
from dnd_combat_engine.models import Campaign, HostedCampaignStatus, PlayerRole


def test_host_and_guest_apps_complete_local_hosted_campaign_loopback(tmp_path: Path) -> None:
    """Two app instances share a hosted session through the local persistence boundary."""
    host_app = create_app(tmp_path)
    campaign = Campaign("loopback", "Loopback Campaign")
    host_app.campaigns.save(campaign)

    hosted = host_app.hosted_campaigns.host_campaign(campaign, "Dungeon Master")

    guest_app = create_app(tmp_path)
    discovered = guest_app.hosted_campaigns.find_session_by_join_code(
        f"{hosted.join_code[:3]}-{hosted.join_code[3:]}"
    )
    assert discovered == hosted

    joined = guest_app.hosted_campaigns.join_session(
        hosted.join_code,
        "fluxor",
        "Fluxor",
        character_id="fluxor",
        role=PlayerRole.PLAYER,
    )
    assert tuple(player.player_id for player in joined.players) == ("host", "fluxor")
    assert host_app.hosted_campaigns.load_session(hosted.session_id) == joined

    live = host_app.hosted_campaigns.activate_session(hosted.session_id)
    assert live.status is HostedCampaignStatus.LIVE
    guest_live = guest_app.hosted_campaigns.load_session(hosted.session_id)
    assert guest_live.status is HostedCampaignStatus.LIVE

    left = guest_app.hosted_campaigns.leave_session(hosted.session_id, "fluxor")
    assert tuple(player.player_id for player in left.connected_players) == ("host",)

    closed = host_app.hosted_campaigns.close_session(hosted.session_id)
    assert closed.status is HostedCampaignStatus.CLOSED
    guest_closed = guest_app.hosted_campaigns.load_session(hosted.session_id)
    assert guest_closed.status is HostedCampaignStatus.CLOSED
