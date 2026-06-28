"""Character controller workflows."""

from __future__ import annotations

from dataclasses import dataclass

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.conditions import Condition, ConditionName
from dnd_combat_engine.models.resources import ResourcePool
from dnd_combat_engine.services.character_service import CharacterService
from dnd_combat_engine.services.persistence_service import PersistenceService


@dataclass(frozen=True, slots=True)
class CharacterController:
    """UI-facing character workflow coordinator."""

    character_service: CharacterService
    persistence_service: PersistenceService

    def load(self, character_id: str) -> Character:
        """Load a character by id."""
        return self.persistence_service.load_character(character_id)

    def save(self, character: Character) -> None:
        """Save a character."""
        self.persistence_service.save_character(character)

    def apply_damage(self, character: Character, amount: int, autosave: bool = False) -> int:
        """Apply damage and optionally save the character."""
        applied = self.character_service.apply_damage(character, amount)
        if autosave:
            self.save(character)
        return applied

    def heal(self, character: Character, amount: int, autosave: bool = False) -> int:
        """Heal a character and optionally save it."""
        restored = self.character_service.heal(character, amount)
        if autosave:
            self.save(character)
        return restored

    def add_condition(
        self,
        character: Character,
        condition: Condition,
        autosave: bool = False,
    ) -> None:
        """Apply a condition and optionally save the character."""
        self.character_service.add_condition(character, condition)
        if autosave:
            self.save(character)

    def remove_condition(
        self,
        character: Character,
        name: ConditionName,
        autosave: bool = False,
    ) -> bool:
        """Remove a condition and optionally save the character."""
        removed = self.character_service.remove_condition(character, name)
        if autosave:
            self.save(character)
        return removed

    def set_resource(
        self,
        character: Character,
        resource: ResourcePool,
        autosave: bool = False,
    ) -> None:
        """Set a resource and optionally save the character."""
        self.character_service.set_resource(character, resource)
        if autosave:
            self.save(character)

