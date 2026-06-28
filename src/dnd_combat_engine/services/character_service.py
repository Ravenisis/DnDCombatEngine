"""Character business operations."""

from __future__ import annotations

from dnd_combat_engine.models.character import Character


class CharacterService:
    """Business operations for character state changes."""

    def apply_damage(self, character: Character, amount: int) -> int:
        """Apply damage to a character and return current hit points lost."""
        return character.hit_points.apply_damage(amount)

    def heal(self, character: Character, amount: int) -> int:
        """Heal a character and return the actual amount restored."""
        return character.hit_points.heal(amount)

