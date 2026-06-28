"""Persistence service facade."""

from __future__ import annotations

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.spells import Spell
from dnd_combat_engine.persistence.json_store import JsonFileStore


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
        return Character.from_dict(self.store.load("characters", character_id))

    def list_character_ids(self) -> list[str]:
        """List saved character ids."""
        return self.store.list_ids("characters")

    def save_spell(self, spell: Spell) -> None:
        """Save a spell as a JSON document."""
        self.store.save("spells", spell.spell_id, spell.to_dict())

    def load_spell(self, spell_id: str) -> Spell:
        """Load a spell from a JSON document."""
        return Spell.from_dict(self.store.load("spells", spell_id))

    def list_spell_ids(self) -> list[str]:
        """List saved spell ids."""
        return self.store.list_ids("spells")
