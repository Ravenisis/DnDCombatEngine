"""WebSocket relay transport for hosted-campaign session lifecycle messages."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from dnd_combat_engine.models import Campaign
from dnd_combat_engine.models.multiplayer import PlayerRole
from dnd_combat_engine.services.hosted_campaign_backend import HostedCampaignBackend


class HostedCampaignWebSocketRelay:
    """Expose hosted-campaign lifecycle operations over a WebSocket connection."""

    def __init__(self, backend: HostedCampaignBackend) -> None:
        """Create a relay backed by one authoritative hosted-campaign backend."""
        self._backend = backend

    async def handle_connection(self, websocket: Any) -> None:
        """Process request/response JSON frames for one connected client."""
        async for message in websocket:
            response = self.dispatch(_json_object(message))
            await websocket.send(json.dumps(response, separators=(",", ":")))

    def dispatch(self, request: Mapping[str, object]) -> dict[str, object]:
        """Run one relay request and return a JSON-compatible response."""
        try:
            action = _required_text(request, "action")
            session = self._dispatch_action(action, request)
        except (KeyError, TypeError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "session": session.to_dict() if session is not None else None}

    def _dispatch_action(self, action: str, request: Mapping[str, object]) -> Any:
        if action == "host":
            campaign_data = _required_object(request, "campaign")
            return self._backend.host_campaign(
                Campaign.from_dict(campaign_data),
                _required_text(request, "host_display_name"),
                max_players=int(request.get("max_players", 8)),
                relay_url=_optional_text(request, "relay_url"),
            )
        if action == "find":
            return self._backend.find_session_by_join_code(_required_text(request, "join_code"))
        if action == "load":
            return self._backend.load_session(_required_text(request, "session_id"))
        if action == "join":
            role = PlayerRole(str(request.get("role", PlayerRole.PLAYER.value)))
            return self._backend.join_session(
                _required_text(request, "join_code"),
                _required_text(request, "player_id"),
                _required_text(request, "display_name"),
                character_id=_optional_text(request, "character_id"),
                role=role,
            )
        if action == "activate":
            return self._backend.activate_session(_required_text(request, "session_id"))
        if action == "leave":
            return self._backend.leave_session(
                _required_text(request, "session_id"), _required_text(request, "player_id")
            )
        if action == "close":
            return self._backend.close_session(_required_text(request, "session_id"))
        raise ValueError(f"unsupported relay action: {action}")


async def send_relay_request(url: str, request: Mapping[str, object]) -> dict[str, object]:
    """Send one request to a relay and return its parsed response frame."""
    from websockets.asyncio.client import connect

    async with connect(url) as websocket:
        await websocket.send(json.dumps(dict(request), separators=(",", ":")))
        return _json_object(await websocket.recv())


async def start_local_relay(
    relay: HostedCampaignWebSocketRelay,
    host: str = "127.0.0.1",
    port: int = 0,
) -> Any:
    """Start a relay listener, using port zero for an OS-selected local port."""
    from websockets.asyncio.server import serve

    return await serve(relay.handle_connection, host, port)


def _json_object(value: object) -> dict[str, object]:
    if not isinstance(value, str):
        raise ValueError("relay messages must be text JSON")
    data = json.loads(value)
    if not isinstance(data, dict):
        raise ValueError("relay messages must contain a JSON object")
    return {str(key): item for key, item in data.items()}


def _required_object(request: Mapping[str, object], key: str) -> dict[str, object]:
    value = request.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return {str(item_key): item_value for item_key, item_value in value.items()}


def _required_text(request: Mapping[str, object], key: str) -> str:
    value = _optional_text(request, key)
    if value is None:
        raise ValueError(f"{key} is required")
    return value


def _optional_text(request: Mapping[str, object], key: str) -> str | None:
    value = request.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be non-empty text")
    return value.strip()
