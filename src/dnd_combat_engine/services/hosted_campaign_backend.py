"""Hosted campaign backend boundary.

This module keeps multiplayer session orchestration behind a small backend
interface. The desktop app can use the local JSON-backed backend today, while a
future internet relay can implement the same interface without changing the GUI.
"""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from dnd_combat_engine.models import Campaign
from dnd_combat_engine.models.multiplayer import (
    HostedCampaignSession,
    HostedCampaignState,
    PlayerRole,
    SessionEventKind,
    SessionStateEvent,
)
from dnd_combat_engine.services.multiplayer_service import MultiplayerService
from dnd_combat_engine.services.persistence_service import PersistenceService


class HostedCampaignBackend(Protocol):
    """Backend operations required by campaign hosting UI."""

    def host_campaign(
        self,
        campaign: Campaign,
        host_display_name: str,
        *,
        max_players: int = 8,
        relay_url: str | None = None,
    ) -> HostedCampaignSession:
        """Create and persist a hosted campaign session."""

    def load_session(self, session_id: str) -> HostedCampaignSession:
        """Load a hosted campaign session by internal session id."""

    def find_session_by_join_code(self, join_code: str) -> HostedCampaignSession | None:
        """Find an open hosted session by human-readable join code."""

    def activate_session(self, session_id: str) -> HostedCampaignSession:
        """Mark a hosted campaign session live."""

    def join_session(
        self,
        join_code: str,
        player_id: str,
        display_name: str,
        *,
        character_id: str | None = None,
        role: PlayerRole = PlayerRole.PLAYER,
    ) -> HostedCampaignSession:
        """Join an open hosted campaign session by join code."""

    def leave_session(self, session_id: str, player_id: str) -> HostedCampaignSession:
        """Disconnect a player from a hosted campaign session."""

    def close_session(self, session_id: str) -> HostedCampaignSession:
        """Close a hosted campaign session."""

    def load_state(self, session_id: str) -> HostedCampaignState:
        """Load the latest synchronized combat state."""

    def publish_state_event(
        self,
        session_id: str,
        source_player_id: str,
        kind: SessionEventKind,
        payload: dict[str, object],
        *,
        character_id: str | None = None,
    ) -> tuple[SessionStateEvent, HostedCampaignState]:
        """Validate, persist, and return one synchronized state event."""


class LocalHostedCampaignBackend:
    """JSON-backed hosted campaign backend for local desktop development."""

    def __init__(
        self,
        persistence: PersistenceService,
        multiplayer: MultiplayerService | None = None,
    ) -> None:
        """Create a backend backed by the app's persistence service."""
        self._persistence = persistence
        self._multiplayer = multiplayer or MultiplayerService()

    def host_campaign(
        self,
        campaign: Campaign,
        host_display_name: str,
        *,
        max_players: int = 8,
        relay_url: str | None = None,
    ) -> HostedCampaignSession:
        """Create, persist, and return a hosted campaign session."""
        session = self._multiplayer.create_hosted_session(
            campaign,
            host_display_name,
            max_players=max_players,
            relay_url=relay_url,
        )
        self._persistence.save_hosted_session(session)
        return session

    def load_session(self, session_id: str) -> HostedCampaignSession:
        """Load a hosted campaign session by internal session id."""
        return self._persistence.load_hosted_session(session_id)

    def find_session_by_join_code(self, join_code: str) -> HostedCampaignSession | None:
        """Find an open hosted session by human-readable join code."""
        for session_id in self._persistence.list_hosted_session_ids():
            session = self._persistence.load_hosted_session(session_id)
            if self._multiplayer.validate_join_code(session, join_code):
                return session
        return None

    def activate_session(self, session_id: str) -> HostedCampaignSession:
        """Mark a hosted campaign session live and persist the change."""
        session = self._multiplayer.activate(self.load_session(session_id))
        self._persistence.save_hosted_session(session)
        return session

    def join_session(
        self,
        join_code: str,
        player_id: str,
        display_name: str,
        *,
        character_id: str | None = None,
        role: PlayerRole = PlayerRole.PLAYER,
    ) -> HostedCampaignSession:
        """Join an open hosted campaign session by join code and persist it."""
        session = self.find_session_by_join_code(join_code)
        if session is None:
            raise ValueError("hosted campaign session not found for join code")
        session = self._multiplayer.join(
            session,
            player_id,
            display_name,
            character_id=character_id,
            role=role,
        )
        self._persistence.save_hosted_session(session)
        return session

    def leave_session(self, session_id: str, player_id: str) -> HostedCampaignSession:
        """Disconnect a player from a hosted campaign session and persist it."""
        session = self._multiplayer.leave(self.load_session(session_id), player_id)
        self._persistence.save_hosted_session(session)
        return session

    def close_session(self, session_id: str) -> HostedCampaignSession:
        """Close a hosted campaign session and persist it."""
        session = self._multiplayer.close(self.load_session(session_id))
        self._persistence.save_hosted_session(session)
        return session

    def load_state(self, session_id: str) -> HostedCampaignState:
        """Load the latest synchronized combat state for a session."""
        self.load_session(session_id)
        return self._persistence.load_hosted_state(session_id)

    def publish_state_event(
        self,
        session_id: str,
        source_player_id: str,
        kind: SessionEventKind,
        payload: dict[str, object],
        *,
        character_id: str | None = None,
    ) -> tuple[SessionStateEvent, HostedCampaignState]:
        """Apply a player's state event to the authoritative session snapshot."""
        session = self.load_session(session_id)
        player = next(
            (
                player
                for player in session.connected_players
                if player.player_id == source_player_id
            ),
            None,
        )
        if player is None:
            raise ValueError("source player is not connected to the hosted session")
        if player.role is PlayerRole.OBSERVER:
            raise ValueError("observers cannot publish campaign state")
        if (
            player.role is not PlayerRole.HOST
            and character_id is not None
            and player.character_id != character_id
        ):
            raise ValueError("players can update only their assigned character")
        state = self._persistence.load_hosted_state(session_id)
        event = SessionStateEvent(
            event_id=uuid4().hex,
            session_id=session_id,
            kind=kind,
            source_player_id=source_player_id,
            character_id=character_id,
            revision=state.revision + 1,
            payload=payload,
        )
        state = state.apply(event)
        self._persistence.save_hosted_state(state)
        return event, state
