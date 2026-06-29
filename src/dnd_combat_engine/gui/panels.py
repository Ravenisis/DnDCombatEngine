"""Pure panel data helpers for GUI widgets."""

from __future__ import annotations

from dnd_combat_engine.controllers import (
    AttackSummary,
    CampaignSummary,
    EncounterSummary,
    InitiativeSummary,
)
from dnd_combat_engine.engine.attacks import AttackResult
from dnd_combat_engine.engine.initiative import InitiativeTracker
from dnd_combat_engine.models.campaigns import Campaign
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.encounters import Encounter


def character_sheet_rows(character: Character) -> list[tuple[str, str]]:
    """Return display rows for a character sheet."""
    return [
        ("Name", character.name),
        ("HP", f"{character.hit_points.current}/{character.hit_points.maximum}"),
        ("Temporary HP", str(character.hit_points.temporary)),
        ("Level", str(character.level)),
        ("Features", ", ".join(character.features)),
    ]


def campaign_rows(campaign: Campaign) -> list[tuple[str, str]]:
    """Return display rows for campaign details."""
    summary = CampaignSummary.from_campaign(campaign)
    return [
        ("Name", summary.name),
        ("Status", summary.status),
        ("Characters", str(summary.character_count)),
        ("Encounters", str(summary.encounter_count)),
        ("Notes", campaign.notes),
    ]


def attack_summary_text(result: AttackResult) -> str:
    """Return a one-line attack summary."""
    summary = AttackSummary.from_result(result)
    outcome = "CRIT" if summary.critical else "HIT" if summary.hit else "MISS"
    return (
        f"{summary.attacker} -> {summary.target} [{outcome}] "
        f"attack={summary.attack_total} damage={summary.damage_total}"
    )


def encounter_rows(encounter: Encounter) -> list[tuple[str, str]]:
    """Return display rows for encounter details."""
    summary = EncounterSummary.from_encounter(encounter)
    return [
        ("Name", summary.name),
        ("Status", summary.status),
        ("Participants", str(summary.participant_count)),
        ("Round", str(summary.round_number)),
    ]


def initiative_rows(tracker: InitiativeTracker) -> list[tuple[str, str]]:
    """Return display rows for initiative order."""
    summary = InitiativeSummary.from_tracker(tracker)
    rows = [("Round", str(summary.round_number)), ("Active", summary.active_combatant or "")]
    rows.extend((str(index), name) for index, name in enumerate(summary.order, start=1))
    return rows
