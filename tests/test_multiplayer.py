import pytest

from dnd_combat_engine.models import (
    Campaign,
    HostedCampaignSession,
    HostedCampaignState,
    HostedCampaignStatus,
    HostedPlayer,
    PlayerRole,
    SessionEventKind,
    SessionStateEvent,
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
        HostedPlayer("host", "")
    with pytest.raises(ValueError):
        HostedPlayer("host", "DM", character_id="")
    with pytest.raises(ValueError):
        HostedCampaignSession("", "starter", "ABC123", "host", players=(host,))
    with pytest.raises(ValueError):
        HostedCampaignSession("session", "", "ABC123", "host", players=(host,))
    with pytest.raises(ValueError):
        HostedCampaignSession("session", "starter", "ABC123", "", players=(host,))
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
    with pytest.raises(ValueError):
        HostedCampaignSession(
            "session", "starter", "ABC123", "host", players=(host,), max_players=0
        )
    with pytest.raises(ValueError):
        HostedCampaignSession(
            "session",
            "starter",
            "ABC123",
            "host",
            players=(host, HostedPlayer("guest", "Guest")),
            max_players=1,
        )
    with pytest.raises(ValueError):
        HostedCampaignSession(
            "session", "starter", "ABC123", "host", players=(host,), relay_url=""
        )
    with pytest.raises(ValueError):
        HostedCampaignSession(
            "session", "starter", "ABC123", "host", players=(host,)
        ).without_player("host")


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


def test_hosted_campaign_state_applies_health_initiative_and_rolls() -> None:
    state = HostedCampaignState("session")
    events = (
        SessionStateEvent(
            "one",
            "session",
            SessionEventKind.CHARACTER_HEALTH,
            "host",
            1,
            {"current": 18, "maximum": 24, "temporary": 3},
            "hero",
        ),
        SessionStateEvent(
            "two",
            "session",
            SessionEventKind.INITIATIVE_ROLL,
            "host",
            2,
            {"total": 17, "natural": 14},
            "hero",
        ),
        SessionStateEvent(
            "three",
            "session",
            SessionEventKind.HIT_ROLL,
            "host",
            3,
            {"total": 22, "natural": 19, "modifier": 3},
            "hero",
        ),
    )

    for event in events:
        state = state.apply(event)
    restored = HostedCampaignState.from_dict(state.to_dict())

    assert restored == state
    assert state.character_health["hero"]["current"] == 18
    assert state.initiative_rolls["hero"] == 17
    assert state.latest_hit_rolls["hero"]["natural"] == 19


def test_session_state_event_validates_payloads_and_revisions() -> None:
    with pytest.raises(ValueError, match="character_id"):
        SessionStateEvent(
            "one", "session", SessionEventKind.HIT_ROLL, "host", 1, {"total": 5, "natural": 1}
        )
    with pytest.raises(ValueError, match="between 1 and 20"):
        SessionStateEvent(
            "one",
            "session",
            SessionEventKind.HIT_ROLL,
            "host",
            1,
            {"total": 24, "natural": 21},
            "hero",
        )
    event = SessionStateEvent(
        "one",
        "session",
        SessionEventKind.ACTION_RESULT,
        "host",
        1,
        {"message": "Hero hits."},
        "hero",
    )
    with pytest.raises(ValueError, match="revision"):
        HostedCampaignState("session", revision=1).apply(event)


def test_party_health_state_and_invalid_event_payloads() -> None:
    party_event = SessionStateEvent(
        "party",
        "session",
        SessionEventKind.PARTY_HEALTH,
        "host",
        1,
        {"members": {"hero": {"current": 7, "maximum": 10, "temporary": 1}}},
    )
    state = HostedCampaignState("session").apply(party_event)
    assert state.character_health["hero"] == {"current": 7, "maximum": 10, "temporary": 1}

    invalid_events = (
        (SessionEventKind.PARTY_HEALTH, {"members": {}}, None),
        (SessionEventKind.PARTY_HEALTH, {"members": {"hero": "bad"}}, None),
        (SessionEventKind.CHARACTER_HEALTH, {"current": 11, "maximum": 10}, "hero"),
        (SessionEventKind.INITIATIVE_ROLL, {"total": True}, "hero"),
        (SessionEventKind.ACTION_RESULT, {"message": ""}, "hero"),
    )
    for kind, payload, character_id in invalid_events:
        with pytest.raises(ValueError):
            SessionStateEvent("bad", "session", kind, "host", 1, payload, character_id)
    with pytest.raises(ValueError, match="payload"):
        SessionStateEvent.from_dict(
            {
                "event_id": "bad",
                "session_id": "session",
                "kind": "initiative_roll",
                "source_player_id": "host",
                "revision": 1,
                "character_id": "hero",
                "payload": "bad",
            }
        )
    with pytest.raises(ValueError, match="different"):
        HostedCampaignState("other").apply(party_event)


def test_session_state_event_rejects_missing_identity_and_revision() -> None:
    with pytest.raises(ValueError, match="ids are required"):
        SessionStateEvent(
            "", "session", SessionEventKind.INITIATIVE_ROLL, "host", 1, {"total": 10}, "hero"
        )
    with pytest.raises(ValueError, match="at least 1"):
        SessionStateEvent(
            "event", "session", SessionEventKind.INITIATIVE_ROLL, "host", 0, {"total": 10}, "hero"
        )
