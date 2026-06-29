"""Controller-backed editing helpers for GUI widgets."""

from __future__ import annotations

from dnd_combat_engine.app import DnDCombatEngineApp


def add_character_to_campaign(
    app: DnDCombatEngineApp,
    campaign_id: str,
    character_id: str,
) -> str:
    """Add a character reference to a campaign and save it."""
    campaign = app.campaigns.load(campaign_id)
    character = app.characters.load(character_id)
    updated = app.campaigns.add_character(campaign, character.character_id)
    app.campaigns.save(updated)
    return f"Added character {character.name} to {updated.name}."


def import_character_pdf_to_campaign(
    app: DnDCombatEngineApp,
    campaign_id: str,
    pdf_path: str,
) -> str:
    """Import a character PDF and add the character to a campaign."""
    result = app.character_imports.import_pdf_to_campaign(pdf_path, campaign_id)
    return (
        f"Imported {result.character.name} as {result.character.character_id} "
        f"and added them to {result.campaign.name}."
    )


def import_character_url_to_campaign(
    app: DnDCombatEngineApp,
    campaign_id: str,
    url: str,
) -> str:
    """Import a character URL and add the character to a campaign."""
    result = app.character_imports.import_url_to_campaign(url, campaign_id)
    return (
        f"Imported {result.character.name} as {result.character.character_id} "
        f"and added them to {result.campaign.name}."
    )


def remove_character_from_campaign(
    app: DnDCombatEngineApp,
    campaign_id: str,
    character_id: str,
) -> str:
    """Remove a character reference from a campaign and save it."""
    campaign = app.campaigns.load(campaign_id)
    updated = app.campaigns.remove_character(campaign, character_id)
    app.campaigns.save(updated)
    return f"Removed character {character_id} from {updated.name}."


def add_encounter_to_campaign(
    app: DnDCombatEngineApp,
    campaign_id: str,
    encounter_id: str,
) -> str:
    """Add an encounter reference to a campaign and save it."""
    campaign = app.campaigns.load(campaign_id)
    encounter = app.encounters.load(encounter_id)
    updated = app.campaigns.add_encounter(campaign, encounter.encounter_id)
    app.campaigns.save(updated)
    return f"Added encounter {encounter.name} to {updated.name}."


def remove_encounter_from_campaign(
    app: DnDCombatEngineApp,
    campaign_id: str,
    encounter_id: str,
) -> str:
    """Remove an encounter reference from a campaign and save it."""
    campaign = app.campaigns.load(campaign_id)
    updated = app.campaigns.remove_encounter(campaign, encounter_id)
    app.campaigns.save(updated)
    return f"Removed encounter {encounter_id} from {updated.name}."


def add_character_to_encounter(
    app: DnDCombatEngineApp,
    encounter_id: str,
    character_id: str,
) -> str:
    """Add a character participant to an encounter and save it."""
    encounter = app.encounters.load(encounter_id)
    character = app.characters.load(character_id)
    updated = app.encounters.add_character(encounter, character)
    app.encounters.save(updated)
    return f"Added {character.name} to {updated.name}."


def add_monster_to_encounter(
    app: DnDCombatEngineApp,
    encounter_id: str,
    monster_id: str,
    quantity: int = 1,
) -> str:
    """Add a monster participant to an encounter and save it."""
    encounter = app.encounters.load(encounter_id)
    monster = app.compendium.load_monster(monster_id)
    updated = app.encounters.add_monster(encounter, monster, quantity=quantity)
    app.encounters.save(updated)
    return f"Added {quantity} {monster.name} to {updated.name}."


def remove_participant_from_encounter(
    app: DnDCombatEngineApp,
    encounter_id: str,
    participant_id: str,
) -> str:
    """Remove a participant from an encounter and save it."""
    encounter = app.encounters.load(encounter_id)
    updated = app.encounters.remove_participant(encounter, participant_id)
    app.encounters.save(updated)
    return f"Removed participant {participant_id} from {updated.name}."


def start_encounter(app: DnDCombatEngineApp, encounter_id: str) -> str:
    """Start an encounter and save its active state."""
    encounter = app.encounters.load(encounter_id)
    active, _ = app.encounters.start_and_roll_initiative(encounter, _characters_for(encounter, app))
    app.encounters.save(active)
    return f"Started {active.name}."


def advance_encounter_round(app: DnDCombatEngineApp, encounter_id: str) -> str:
    """Advance an active encounter and save it."""
    encounter = app.encounters.load(encounter_id)
    updated = app.encounters.advance_round(encounter)
    app.encounters.save(updated)
    return f"Advanced {updated.name} to round {updated.round_number}."


def complete_encounter(app: DnDCombatEngineApp, encounter_id: str) -> str:
    """Complete an encounter and save it."""
    encounter = app.encounters.load(encounter_id)
    updated = app.encounters.complete(encounter)
    app.encounters.save(updated)
    return f"Completed {updated.name}."


def _characters_for(encounter, app: DnDCombatEngineApp):
    return tuple(
        app.characters.load(participant.source_id)
        for participant in encounter.participants
        if participant.kind == "character"
    )
