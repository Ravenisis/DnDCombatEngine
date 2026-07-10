"""Hosted campaign session business operations."""

from __future__ import annotations

import secrets
import string
from dataclasses import replace

from dnd_combat_engine.models import Campaign
from dnd_combat_engine.models.multiplayer import (
    HostedCampaignSession,
    HostedCampaignStatus,
    HostedPlayer,
    PlayerRole,
)

_JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class MultiplayerService:
    """Create and manage hosted campaign session metadata."""

    def create_hosted_session(
        self,
        campaign: Campaign,
        host_display_name: str,
        *,
        max_players: int = 8,
        relay_url: str | None = None,
    ) -> HostedCampaignSession:
        """Create a waiting hosted session for a campaign."""
        join_code = self.generate_join_code()
        host_player = HostedPlayer(
            player_id="host",
            display_name=host_display_name,
            role=PlayerRole.HOST,
            connected=True,
        )
        return HostedCampaignSession(
            session_id=f"{campaign.campaign_id}-{join_code}",
            campaign_id=campaign.campaign_id,
            join_code=join_code,
            host_player_id=host_player.player_id,
            players=(host_player,),
            max_players=max_players,
            relay_url=relay_url,
        )

    def activate(self, session: HostedCampaignSession) -> HostedCampaignSession:
        """Mark a hosted campaign session live."""
        if session.status is HostedCampaignStatus.CLOSED:
            raise ValueError("closed sessions cannot be activated")
        return session.with_status(HostedCampaignStatus.LIVE)

    def close(self, session: HostedCampaignSession) -> HostedCampaignSession:
        """Close a hosted campaign session."""
        return session.with_status(HostedCampaignStatus.CLOSED)

    def join(
        self,
        session: HostedCampaignSession,
        player_id: str,
        display_name: str,
        *,
        character_id: str | None = None,
        role: PlayerRole = PlayerRole.PLAYER,
    ) -> HostedCampaignSession:
        """Add or reconnect a player to a hosted campaign session."""
        if role is PlayerRole.HOST:
            raise ValueError("join cannot create another host")
        player = HostedPlayer(
            player_id=player_id,
            display_name=display_name,
            role=role,
            character_id=character_id,
            connected=True,
        )
        return session.with_player(player)

    def leave(self, session: HostedCampaignSession, player_id: str) -> HostedCampaignSession:
        """Mark a player disconnected from a hosted campaign session."""
        if player_id == session.host_player_id:
            return self.close(session)
        return session.disconnect_player(player_id)

    def remove_player(
        self, session: HostedCampaignSession, player_id: str
    ) -> HostedCampaignSession:
        """Remove a non-host player from a hosted campaign session."""
        return session.without_player(player_id)

    def refresh_join_code(self, session: HostedCampaignSession) -> HostedCampaignSession:
        """Return a session with a new join code."""
        if session.status is HostedCampaignStatus.CLOSED:
            raise ValueError("closed sessions cannot refresh join codes")
        return replace(session, join_code=self.generate_join_code())

    def validate_join_code(self, session: HostedCampaignSession, join_code: str) -> bool:
        """Return whether a user-supplied join code matches a session."""
        return self.normalize_join_code(join_code) == session.join_code

    def generate_join_code(self, length: int = 6) -> str:
        """Generate a short human-readable join code."""
        if length < 4:
            raise ValueError("join code length must be at least 4")
        return "".join(secrets.choice(_JOIN_CODE_ALPHABET) for _ in range(length))

    def normalize_join_code(self, join_code: str) -> str:
        """Normalize join code input from the GUI or clipboard."""
        normalized = "".join(
            character
            for character in join_code.upper()
            if character in string.ascii_uppercase or character.isdigit()
        )
        return normalized.replace("0", "O").replace("1", "I")
