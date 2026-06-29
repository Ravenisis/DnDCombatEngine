"""Models for importing external character sheet data."""

from __future__ import annotations

from dataclasses import dataclass, field

from dnd_combat_engine.models.abilities import AbilityScores
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.equipment import Armor, Weapon
from dnd_combat_engine.models.hit_points import HitPoints
from dnd_combat_engine.models.inventory import InventoryItem


@dataclass(frozen=True, slots=True)
class CharacterImportDraft:
    """Reviewable character data parsed from an external sheet."""

    name: str
    level: int = 1
    hit_points: HitPoints = field(default_factory=lambda: HitPoints(1, 1))
    abilities: AbilityScores = field(default_factory=AbilityScores)
    skills: tuple[str, ...] = field(default_factory=tuple)
    inventory: tuple[InventoryItem, ...] = field(default_factory=tuple)
    weapons: tuple[Weapon, ...] = field(default_factory=tuple)
    armor: Armor | None = None
    source: str = "pdf"

    def to_character(self, character_id: str) -> Character:
        """Convert the draft into a persisted character model."""
        return Character(
            character_id=character_id,
            name=self.name,
            hit_points=self.hit_points,
            abilities=self.abilities,
            level=self.level,
            skills=self.skills,
            inventory=self.inventory,
            weapons=self.weapons,
            armor=self.armor,
        )

