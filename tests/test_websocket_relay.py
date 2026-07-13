"""Localhost integration coverage for the hosted-campaign WebSocket relay."""

from __future__ import annotations

import asyncio
from pathlib import Path

from dnd_combat_engine.models import Campaign, HostedCampaignSession, HostedCampaignStatus
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import (
    HostedCampaignWebSocketRelay,
    LocalHostedCampaignBackend,
    PersistenceService,
)
from dnd_combat_engine.services.websocket_relay import send_relay_request, start_local_relay


def test_local_websocket_relay_hosts_joins_and_closes_campaign(tmp_path: Path) -> None:
    """A host and guest exchange lifecycle commands through a loopback socket."""
    asyncio.run(_run_loopback_relay(tmp_path))


async def _run_loopback_relay(tmp_path: Path) -> None:
    backend = LocalHostedCampaignBackend(PersistenceService(JsonFileStore(tmp_path)))
    server = await start_local_relay(HostedCampaignWebSocketRelay(backend))
    try:
        socket = server.sockets[0]
        host, port = socket.getsockname()[:2]
        url = f"ws://{host}:{port}"
        campaign = Campaign("relay", "Relay Campaign")

        hosted = await send_relay_request(
            url,
            {
                "action": "host",
                "campaign": campaign.to_dict(),
                "host_display_name": "Dungeon Master",
                "relay_url": url,
            },
        )
        session = _response_session(hosted)

        found = await send_relay_request(
            url, {"action": "find", "join_code": f"{session.join_code[:3]}-{session.join_code[3:]}"}
        )
        assert _response_session(found) == session

        joined = await send_relay_request(
            url,
            {
                "action": "join",
                "join_code": session.join_code,
                "player_id": "fluxor",
                "display_name": "Fluxor",
                "character_id": "fluxor",
            },
        )
        joined_session = _response_session(joined)
        assert tuple(player.player_id for player in joined_session.players) == ("host", "fluxor")

        live = await send_relay_request(
            url, {"action": "activate", "session_id": session.session_id}
        )
        assert _response_session(live).status is HostedCampaignStatus.LIVE

        left = await send_relay_request(
            url, {"action": "leave", "session_id": session.session_id, "player_id": "fluxor"}
        )
        left_session = _response_session(left)
        assert tuple(player.player_id for player in left_session.connected_players) == ("host",)

        closed = await send_relay_request(
            url, {"action": "close", "session_id": session.session_id}
        )
        assert _response_session(closed).status is HostedCampaignStatus.CLOSED
    finally:
        server.close()
        await server.wait_closed()


def _response_session(response: dict[str, object]) -> HostedCampaignSession:
    assert response["ok"] is True
    payload = response["session"]
    assert isinstance(payload, dict)
    return HostedCampaignSession.from_dict(payload)
