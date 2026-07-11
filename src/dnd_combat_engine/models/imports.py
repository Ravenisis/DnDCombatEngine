"""Models for importing external character sheet data."""

from __future__ import annotations

from dataclasses import dataclass, field

from dnd_combat_engine.models.abilities import AbilityScores
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.currency import CurrencyPurse
from dnd_combat_engine.models.damage import DamageType
from dnd_combat_engine.models.equipment import Armor, Weapon
from dnd_combat_engine.models.hit_points import HitPoints
from dnd_combat_engine.models.inventory import InventoryItem
from dnd_combat_engine.models.resources import ResourcePool
from dnd_combat_engine.models.rules import RuleSource


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
    features: tuple[str, ...] = field(default_factory=tuple)
    currency: CurrencyPurse = field(default_factory=CurrencyPurse)
    resources: dict[str, ResourcePool] = field(default_factory=dict)
    saving_throw_proficiencies: tuple[str, ...] = field(default_factory=tuple)
    armor_proficiencies: tuple[str, ...] = field(default_factory=tuple)
    weapon_proficiencies: tuple[str, ...] = field(default_factory=tuple)
    tool_proficiencies: tuple[str, ...] = field(default_factory=tuple)
    languages: tuple[str, ...] = field(default_factory=tuple)
    damage_resistances: tuple[DamageType, ...] = field(default_factory=tuple)
    source: str = "pdf"
    rule_source: RuleSource | None = None

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
            features=self.features,
            currency=self.currency,
            resources=dict(self.resources),
            saving_throw_proficiencies=self.saving_throw_proficiencies,
            armor_proficiencies=self.armor_proficiencies,
            weapon_proficiencies=self.weapon_proficiencies,
            tool_proficiencies=self.tool_proficiencies,
            languages=self.languages,
            damage_resistances=self.damage_resistances,
        )
