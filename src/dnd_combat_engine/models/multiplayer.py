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


class SessionEventKind(StrEnum):
    """Authoritative state changes shared by connected campaign clients."""

    CHARACTER_HEALTH = "character_health"
    PARTY_HEALTH = "party_health"
    INITIATIVE_ROLL = "initiative_roll"
    HIT_ROLL = "hit_roll"
    ACTION_RESULT = "action_result"


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


@dataclass(frozen=True, slots=True)
class SessionStateEvent:
    """One revisioned change to shared hosted-campaign state."""

    event_id: str
    session_id: str
    kind: SessionEventKind
    source_player_id: str
    revision: int
    payload: dict[str, object]
    character_id: str | None = None

    def __post_init__(self) -> None:
        """Validate event identity and the payload required by its kind."""
        if not self.event_id or not self.session_id or not self.source_player_id:
            raise ValueError("event, session, and source player ids are required")
        if self.revision < 1:
            raise ValueError("event revision must be at least 1")
        if self.kind is not SessionEventKind.PARTY_HEALTH and not self.character_id:
            raise ValueError(f"character_id is required for {self.kind.value}")
        _validate_event_payload(self.kind, self.payload)

    def to_dict(self) -> dict[str, object]:
        """Serialize the event to JSON-compatible data."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "kind": self.kind.value,
            "source_player_id": self.source_player_id,
            "character_id": self.character_id,
            "revision": self.revision,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build an event from JSON-compatible data."""
        payload = data.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("event payload must be an object")
        character_id = data.get("character_id")
        return cls(
            event_id=str(data["event_id"]),
            session_id=str(data["session_id"]),
            kind=SessionEventKind(str(data["kind"])),
            source_player_id=str(data["source_player_id"]),
            character_id=str(character_id) if character_id is not None else None,
            revision=int(data["revision"]),
            payload={str(key): value for key, value in payload.items()},
        )


@dataclass(frozen=True, slots=True)
class HostedCampaignState:
    """Latest synchronized combat state for a hosted campaign session."""

    session_id: str
    revision: int = 0
    character_health: dict[str, dict[str, int]] = field(default_factory=dict)
    initiative_rolls: dict[str, int] = field(default_factory=dict)
    latest_hit_rolls: dict[str, dict[str, object]] = field(default_factory=dict)
    recent_events: tuple[SessionStateEvent, ...] = field(default_factory=tuple)

    def apply(self, event: SessionStateEvent) -> Self:
        """Return state with the next authoritative event applied."""
        if event.session_id != self.session_id:
            raise ValueError("event belongs to a different hosted session")
        if event.revision != self.revision + 1:
            raise ValueError("event revision is not the next session revision")
        health = {key: dict(value) for key, value in self.character_health.items()}
        initiative = dict(self.initiative_rolls)
        hit_rolls = {key: dict(value) for key, value in self.latest_hit_rolls.items()}
        if event.kind is SessionEventKind.CHARACTER_HEALTH and event.character_id:
            health[event.character_id] = _health_payload(event.payload)
        elif event.kind is SessionEventKind.PARTY_HEALTH:
            members = event.payload["members"]
            if isinstance(members, dict):
                health.update(
                    {
                        str(character_id): _health_payload(value)
                        for character_id, value in members.items()
                        if isinstance(value, dict)
                    }
                )
        elif event.kind is SessionEventKind.INITIATIVE_ROLL and event.character_id:
            initiative[event.character_id] = int(event.payload["total"])
        elif (
            event.kind in {SessionEventKind.HIT_ROLL, SessionEventKind.ACTION_RESULT}
            and event.character_id
        ):
            hit_rolls[event.character_id] = dict(event.payload)
        return type(self)(
            session_id=self.session_id,
            revision=event.revision,
            character_health=health,
            initiative_rolls=initiative,
            latest_hit_rolls=hit_rolls,
            recent_events=(*self.recent_events[-99:], event),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize synchronized state to JSON-compatible data."""
        return {
            SCHEMA_VERSION_FIELD: CURRENT_SCHEMA_VERSION,
            "session_id": self.session_id,
            "revision": self.revision,
            "character_health": self.character_health,
            "initiative_rolls": self.initiative_rolls,
            "latest_hit_rolls": self.latest_hit_rolls,
            "recent_events": [event.to_dict() for event in self.recent_events],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build synchronized state from JSON-compatible data."""
        return cls(
            session_id=str(data["session_id"]),
            revision=int(data.get("revision", 0)),
            character_health=_nested_int_mapping(data.get("character_health", {})),
            initiative_rolls={
                str(key): int(value)
                for key, value in _mapping(data.get("initiative_rolls", {})).items()
            },
            latest_hit_rolls={
                str(key): dict(value)
                for key, value in _mapping(data.get("latest_hit_rolls", {})).items()
                if isinstance(value, dict)
            },
            recent_events=tuple(
                SessionStateEvent.from_dict(value)
                for value in data.get("recent_events", [])
                if isinstance(value, dict)
            ),
        )


def _validate_event_payload(kind: SessionEventKind, payload: dict[str, object]) -> None:
    if kind is SessionEventKind.CHARACTER_HEALTH:
        _health_payload(payload)
    elif kind is SessionEventKind.PARTY_HEALTH:
        members = payload.get("members")
        if not isinstance(members, dict) or not members:
            raise ValueError("party health requires a non-empty members object")
        for value in members.values():
            if not isinstance(value, dict):
                raise ValueError("party health member values must be objects")
            _health_payload(value)
    elif kind is SessionEventKind.INITIATIVE_ROLL:
        _required_int(payload, "total")
    elif kind is SessionEventKind.HIT_ROLL:
        _required_int(payload, "total")
        natural = _required_int(payload, "natural")
        if not 1 <= natural <= 20:
            raise ValueError("hit roll natural value must be between 1 and 20")
    elif kind is SessionEventKind.ACTION_RESULT and (
        not isinstance(payload.get("message"), str) or not payload["message"]
    ):
        raise ValueError("action result requires a message")


def _health_payload(payload: object) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError("health payload must be an object")
    current = _required_int(payload, "current")
    maximum = _required_int(payload, "maximum")
    temporary = int(payload.get("temporary", 0))
    if maximum < 1 or current < 0 or current > maximum or temporary < 0:
        raise ValueError("health values are outside their valid range")
    return {"current": current, "maximum": maximum, "temporary": temporary}


def _required_int(payload: dict[str, object], name: str) -> int:
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _mapping(value: object) -> dict[object, object]:
    return value if isinstance(value, dict) else {}


def _nested_int_mapping(value: object) -> dict[str, dict[str, int]]:
    return {
        str(key): {str(inner_key): int(inner_value) for inner_key, inner_value in inner.items()}
        for key, inner in _mapping(value).items()
        if isinstance(inner, dict)
    }
