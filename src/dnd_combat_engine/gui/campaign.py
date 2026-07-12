"""Campaign GUI state and small campaign-selection helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from dnd_combat_engine.models.concentration import ConcentrationState
from dnd_combat_engine.models.effects import TargetReference


@dataclass(slots=True)
class GuiCampaignState:
    """Mutable GUI state for the currently open campaign workspace."""

    active_campaign_id: str | None = "starter_campaign"
    selected_character_id: str | None = "ravenisis"
    party_leader_character_id: str | None = "ravenisis"
    party_initiative: dict[str, int] = field(default_factory=dict)
    concentration_character_id: str | None = None
    concentration_spell_id: str | None = None
    active_concentration: ConcentrationState | None = None
    beacon_of_hope_targets: tuple[str, ...] = field(default_factory=tuple)
    bless_targets: tuple[str, ...] = field(default_factory=tuple)
    active_target: TargetReference | None = None
    last_dice_notation: str = "1d20"
    pending_action_check: tuple[int, str, bool, bool] | None = None


def active_character_id(state: GuiCampaignState) -> str | None:
    """Return the party leader, falling back to the selected character."""
    return state.party_leader_character_id or state.selected_character_id


def slug(value: str) -> str:
    """Normalize a display name into a persistence-safe identifier."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def unique_campaign_id(app: Any, name: str) -> str:
    """Return a stable unused campaign identifier for a display name."""
    base = slug(name) or "campaign"
    candidate = base
    index = 2
    existing = set(app.campaigns.list_ids())
    while candidate in existing:
        candidate = f"{base}_{index}"
        index += 1
    return candidate
