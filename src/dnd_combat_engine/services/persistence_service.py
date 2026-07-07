"""Persistence service facade."""

from __future__ import annotations

from dnd_combat_engine.models.campaigns import Campaign
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.effects import EffectDefinition
from dnd_combat_engine.models.encounters import Encounter
from dnd_combat_engine.models.monsters import Monster
from dnd_combat_engine.models.spells import Spell
from dnd_combat_engine.persistence.json_store import JsonFileStore
from dnd_combat_engine.persistence.migrations import (
    migrate_campaign,
    migrate_character,
    migrate_encounter,
    migrate_monster,
    migrate_spell,
)


class PersistenceService:
    """Typed persistence operations for domain models."""

    def __init__(self, store: JsonFileStore) -> None:
        """Create the service around a JSON store."""
        self.store = store

    def save_character(self, character: Character) -> None:
        """Save a character as a JSON document."""
        self.store.save("characters", character.character_id, character.to_dict())

    def load_character(self, character_id: str) -> Character:
        """Load a character from a JSON document."""
        return Character.from_dict(migrate_character(self.store.load("characters", character_id)))

    def list_character_ids(self) -> list[str]:
        """List saved character ids."""
        return self.store.list_ids("characters")

    def save_campaign(self, campaign: Campaign) -> None:
        """Save a campaign as a JSON document."""
        self.store.save("campaigns", campaign.campaign_id, campaign.to_dict())

    def load_campaign(self, campaign_id: str) -> Campaign:
        """Load a campaign from a JSON document."""
        return Campaign.from_dict(migrate_campaign(self.store.load("campaigns", campaign_id)))

    def list_campaign_ids(self) -> list[str]:
        """List saved campaign ids."""
        return self.store.list_ids("campaigns")

    def save_spell(self, spell: Spell) -> None:
        """Save a spell as a JSON document."""
        self.store.save("spells", spell.spell_id, spell.to_dict())

    def load_spell(self, spell_id: str) -> Spell:
        """Load a spell from a JSON document."""
        return Spell.from_dict(migrate_spell(self.store.load("spells", spell_id)))

    def list_spell_ids(self) -> list[str]:
        """List saved spell ids."""
        return self.store.list_ids("spells")

    def load_action_effect(self, action_id: str) -> EffectDefinition:
        """Load a standalone action effect definition from a JSON document."""
        return EffectDefinition.from_dict(self.store.load("actions", action_id))

    def list_action_effect_ids(self) -> list[str]:
        """List saved standalone action effect ids."""
        return self.store.list_ids("actions")

    def save_monster(self, monster: Monster) -> None:
        """Save a monster as a JSON document."""
        self.store.save("monsters", monster.monster_id, monster.to_dict())

    def load_monster(self, monster_id: str) -> Monster:
        """Load a monster from a JSON document."""
        return Monster.from_dict(migrate_monster(self.store.load("monsters", monster_id)))

    def list_monster_ids(self) -> list[str]:
        """List saved monster ids."""
        return self.store.list_ids("monsters")

    def save_encounter(self, encounter: Encounter) -> None:
        """Save an encounter as a JSON document."""
        self.store.save("encounters", encounter.encounter_id, encounter.to_dict())

    def load_encounter(self, encounter_id: str) -> Encounter:
        """Load an encounter from a JSON document."""
        return Encounter.from_dict(migrate_encounter(self.store.load("encounters", encounter_id)))

    def list_encounter_ids(self) -> list[str]:
        """List saved encounter ids."""
        return self.store.list_ids("encounters")
