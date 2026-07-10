import pytest

from dnd_combat_engine.models import (
    Campaign,
    HostedCampaignSession,
    HostedCampaignStatus,
    HostedPlayer,
    PlayerRole,
)
from dnd_combat_engine.models.schema import SCHEMA_VERSION_FIELD
from dnd_combat_engine.services import MultiplayerService


def test_hosted_campaign_session_round_trips_to_plain_data() -> None:
    session = HostedCampaignSession(
        session_id="starter-ABC123",
        campaign_id="starter",
        join_code="ABC123",
        host_player_id="host",
        status=HostedCampaignStatus.LIVE,
        players=(
            HostedPlayer("host", "Dungeon Master", PlayerRole.HOST),
            HostedPlayer("fluxor", "Fluxor", character_id="fluxor"),
        ),
        relay_url="wss://relay.example.test/campaigns",
    )

    payload = session.to_dict()
    restored = HostedCampaignSession.from_dict(payload)

    assert payload[SCHEMA_VERSION_FIELD] == 1
    assert restored == session


def test_multiplayer_service_creates_host_session_and_join_code() -> None:
    service = MultiplayerService()
    session = service.create_hosted_session(Campaign("starter", "Starter"), "Ravenisis")

    assert session.campaign_id == "starter"
    assert session.status is HostedCampaignStatus.WAITING
    assert len(session.join_code) == 6
    assert session.players == (HostedPlayer("host", "Ravenisis", PlayerRole.HOST),)
    assert service.validate_join_code(session, f" {session.join_code[:3]}-{session.join_code[3:]} ")


def test_multiplayer_service_manages_player_lifecycle() -> None:
    service = MultiplayerService()
    session = service.create_hosted_session(Campaign("starter", "Starter"), "DM")

    session = service.join(session, "fluxor", "Fluxor", character_id="fluxor")
    live = service.activate(session)
    disconnected = service.leave(live, "fluxor")
    removed = service.remove_player(disconnected, "fluxor")
    closed = service.leave(removed, "host")

    assert live.status is HostedCampaignStatus.LIVE
    assert disconnected.connected_players == (HostedPlayer("host", "DM", PlayerRole.HOST),)
    assert tuple(player.player_id for player in removed.players) == ("host",)
    assert closed.status is HostedCampaignStatus.CLOSED


def test_hosted_campaign_session_rejects_invalid_values() -> None:
    host = HostedPlayer("host", "DM", PlayerRole.HOST)
    with pytest.raises(ValueError):
        HostedPlayer("", "DM")
    with pytest.raises(ValueError):
        HostedCampaignSession("", "starter", "ABC123", "host", players=(host,))
    with pytest.raises(ValueError):
        HostedCampaignSession("session", "", "ABC123", "host", players=(host,))
    with pytest.raises(ValueError):
        HostedCampaignSession("session", "starter", "", "host", players=(host,))
    with pytest.raises(ValueError):
        HostedCampaignSession("session", "starter", "ABC123", "missing", players=(host,))
    with pytest.raises(ValueError):
        HostedCampaignSession(
            "session",
            "starter",
            "ABC123",
            "host",
            players=(host, HostedPlayer("host", "Duplicate")),
        )


def test_multiplayer_service_rejects_full_or_closed_sessions() -> None:
    service = MultiplayerService()
    session = service.create_hosted_session(
        Campaign("starter", "Starter"), "DM", max_players=1
    )

    with pytest.raises(ValueError):
        service.join(session, "fluxor", "Fluxor")
    with pytest.raises(ValueError):
        service.join(session, "other-host", "Other Host", role=PlayerRole.HOST)

    closed = service.close(session)
    with pytest.raises(ValueError):
        service.join(closed, "fluxor", "Fluxor")
    with pytest.raises(ValueError):
        service.activate(closed)
    with pytest.raises(ValueError):
        service.refresh_join_code(closed)
