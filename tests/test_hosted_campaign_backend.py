from pathlib import Path

import pytest

from dnd_combat_engine.models import Campaign, HostedCampaignStatus, PlayerRole
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import LocalHostedCampaignBackend, PersistenceService


def _backend(root: Path) -> LocalHostedCampaignBackend:
    return LocalHostedCampaignBackend(PersistenceService(JsonFileStore(root)))


def test_local_hosted_campaign_backend_hosts_and_discovers_by_join_code(
    tmp_path: Path,
) -> None:
    backend = _backend(tmp_path)

    session = backend.host_campaign(Campaign("starter", "Starter"), "Ravenisis")
    found = backend.find_session_by_join_code(f"{session.join_code[:3]}-{session.join_code[3:]}")

    assert found == session
    assert backend.load_session(session.session_id) == session
    assert session.status is HostedCampaignStatus.WAITING


def test_local_hosted_campaign_backend_manages_join_leave_and_close(tmp_path: Path) -> None:
    backend = _backend(tmp_path)
    session = backend.host_campaign(Campaign("starter", "Starter"), "DM")

    joined = backend.join_session(
        session.join_code,
        "fluxor",
        "Fluxor",
        character_id="fluxor",
        role=PlayerRole.PLAYER,
    )
    live = backend.activate_session(joined.session_id)
    left = backend.leave_session(live.session_id, "fluxor")
    closed = backend.close_session(left.session_id)

    assert tuple(player.player_id for player in joined.players) == ("host", "fluxor")
    assert live.status is HostedCampaignStatus.LIVE
    assert tuple(player.player_id for player in left.connected_players) == ("host",)
    assert closed.status is HostedCampaignStatus.CLOSED
    assert backend.load_session(closed.session_id) == closed


def test_local_hosted_campaign_backend_rejects_unknown_join_code(tmp_path: Path) -> None:
    backend = _backend(tmp_path)

    with pytest.raises(ValueError, match="join code"):
        backend.join_session("MISSING", "fluxor", "Fluxor")
