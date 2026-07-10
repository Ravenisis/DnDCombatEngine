"""Multiplayer campaign session models."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Self

from dnd_combat_engine.models.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_FIELD


class HostedCampaignStatus(StrEnum):
    """Lifecycle state for an internet-hosted campaign session."""

    WAITING = "waiting"
    LIVE = "live"
    CLOSED = "closed"


class PlayerRole(StrEnum):
    """Permission level for a player connected to a hosted campaign."""

    HOST = "host"
    PLAYER = "player"
    OBSERVER = "observer"


@dataclass(frozen=True, slots=True)
class HostedPlayer:
    """A player entry in a hosted campaign session."""

    player_id: str
    display_name: str
    role: PlayerRole = PlayerRole.PLAYER
    character_id: str | None = None
    connected: bool = True

    def __post_init__(self) -> None:
        """Validate hosted player fields."""
        if not self.player_id:
            raise ValueError("player_id is required")
        if not self.display_name:
            raise ValueError("display_name is required")
        if self.character_id == "":
            raise ValueError("character_id cannot be blank")

    def as_disconnected(self) -> Self:
        """Return a copy of the player marked disconnected."""
        return replace(self, connected=False)

    def to_dict(self) -> dict[str, object]:
        """Serialize the player to plain JSON-compatible data."""
        return {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "role": self.role.value,
            "character_id": self.character_id,
            "connected": self.connected,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a player from JSON-compatible data."""
        character_id = data.get("character_id")
        return cls(
            player_id=str(data["player_id"]),
            display_name=str(data["display_name"]),
            role=PlayerRole(str(data.get("role", PlayerRole.PLAYER.value))),
            character_id=str(character_id) if character_id is not None else None,
            connected=bool(data.get("connected", True)),
        )


@dataclass(frozen=True, slots=True)
class HostedCampaignSession:
    """A shareable hosted campaign session with a join code."""

    session_id: str
    campaign_id: str
    join_code: str
    host_player_id: str
    status: HostedCampaignStatus = HostedCampaignStatus.WAITING
    players: tuple[HostedPlayer, ...] = field(default_factory=tuple)
    max_players: int = 8
    relay_url: str | None = None

    def __post_init__(self) -> None:
        """Validate hosted campaign session fields."""
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.campaign_id:
            raise ValueError("campaign_id is required")
        if not self.join_code:
            raise ValueError("join_code is required")
        if not self.host_player_id:
            raise ValueError("host_player_id is required")
        if self.max_players < 1:
            raise ValueError("max_players must be at least 1")
        if len(self.players) > self.max_players:
            raise ValueError("players cannot exceed max_players")
        if len({player.player_id for player in self.players}) != len(self.players):
            raise ValueError("players cannot contain duplicate ids")
        if self.host_player_id not in {player.player_id for player in self.players}:
            raise ValueError("host_player_id must reference a hosted player")
        if self.relay_url == "":
            raise ValueError("relay_url cannot be blank")

    @property
    def connected_players(self) -> tuple[HostedPlayer, ...]:
        """Return players currently marked connected."""
        return tuple(player for player in self.players if player.connected)

    def with_player(self, player: HostedPlayer) -> Self:
        """Return a session with a player added or reconnected."""
        if self.status is HostedCampaignStatus.CLOSED:
            raise ValueError("closed sessions cannot accept players")
        existing = {item.player_id: item for item in self.players}
        if player.player_id not in existing and len(self.players) >= self.max_players:
            raise ValueError("hosted campaign session is full")
        players = tuple(
            player if item.player_id == player.player_id else item for item in self.players
        )
        if player.player_id not in existing:
            players = (*self.players, player)
        return replace(self, players=players)

    def without_player(self, player_id: str) -> Self:
        """Return a session with a non-host player removed."""
        if player_id == self.host_player_id:
            raise ValueError("host player cannot be removed from the session")
        return replace(
            self,
            players=tuple(player for player in self.players if player.player_id != player_id),
        )

    def disconnect_player(self, player_id: str) -> Self:
        """Return a session with a player marked disconnected."""
        return replace(
            self,
            players=tuple(
                player.as_disconnected() if player.player_id == player_id else player
                for player in self.players
            ),
        )

    def with_status(self, status: HostedCampaignStatus) -> Self:
        """Return a session with a new lifecycle status."""
        return replace(self, status=status)

    def to_dict(self) -> dict[str, object]:
        """Serialize the session to plain JSON-compatible data."""
        return {
            SCHEMA_VERSION_FIELD: CURRENT_SCHEMA_VERSION,
            "session_id": self.session_id,
            "campaign_id": self.campaign_id,
            "join_code": self.join_code,
            "host_player_id": self.host_player_id,
            "status": self.status.value,
            "players": [player.to_dict() for player in self.players],
            "max_players": self.max_players,
            "relay_url": self.relay_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a session from JSON-compatible data."""
        return cls(
            session_id=str(data["session_id"]),
            campaign_id=str(data["campaign_id"]),
            join_code=str(data["join_code"]),
            host_player_id=str(data["host_player_id"]),
            status=HostedCampaignStatus(
                str(data.get("status", HostedCampaignStatus.WAITING.value))
            ),
            players=tuple(
                HostedPlayer.from_dict(player) for player in data.get("players", [])
            ),
            max_players=int(data.get("max_players", 8)),
            relay_url=(
                str(data["relay_url"]) if data.get("relay_url") is not None else None
            ),
        )
