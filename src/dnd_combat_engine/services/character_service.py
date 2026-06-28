"""Character business operations."""

from __future__ import annotations

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.conditions import Condition, ConditionName
from dnd_combat_engine.models.resources import ResourcePool


class CharacterService:
    """Business operations for character state changes."""

    def apply_damage(self, character: Character, amount: int) -> int:
        """Apply damage to a character and return current hit points lost."""
        return character.hit_points.apply_damage(amount)

    def heal(self, character: Character, amount: int) -> int:
        """Heal a character and return the actual amount restored."""
        return character.hit_points.heal(amount)

    def add_condition(self, character: Character, condition: Condition) -> None:
        """Apply a condition to a character if it is not already present."""
        if not self.has_condition(character, condition.name):
            character.conditions = (*character.conditions, condition)

    def remove_condition(self, character: Character, name: ConditionName) -> bool:
        """Remove a condition by name and return whether one was removed."""
        before = len(character.conditions)
        character.conditions = tuple(
            condition for condition in character.conditions if condition.name != name
        )
        return len(character.conditions) != before

    def has_condition(self, character: Character, name: ConditionName) -> bool:
        """Return whether a character currently has a condition."""
        return any(condition.name == name for condition in character.conditions)

    def tick_conditions(self, character: Character) -> None:
        """Advance timed conditions by one round and remove expired entries."""
        remaining = []
        for condition in character.conditions:
            ticked = condition.tick_round()
            if ticked is not None:
                remaining.append(ticked)
        character.conditions = tuple(remaining)

    def set_resource(self, character: Character, resource: ResourcePool) -> None:
        """Set or replace a character resource pool."""
        character.resources[resource.name] = resource

    def expend_resource(self, character: Character, name: str, amount: int = 1) -> bool:
        """Spend a named resource if it exists and has enough uses."""
        resource = character.resources.get(name)
        return resource.expend(amount) if resource is not None else False

    def restore_resource(self, character: Character, name: str, amount: int) -> int:
        """Restore a named resource and return the actual amount restored."""
        resource = character.resources.get(name)
        return resource.restore(amount) if resource is not None else 0
