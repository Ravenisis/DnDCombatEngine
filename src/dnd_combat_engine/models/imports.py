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
    character_class: str = ""
    race: str = ""
    senses: tuple[str, ...] = field(default_factory=tuple)
    initiative_modifier: int | None = None
    heroic_inspiration: bool = False
    proficiency_bonus: int | None = None
    ability_save_dc: int | None = None
    walking_speed: int | None = None
    spellcasting_ability: str = ""
    spell_save_dc: int | None = None
    spell_attack_bonus: int | None = None
    saving_throw_modifiers: dict[str, int] = field(default_factory=dict)
    skills: tuple[str, ...] = field(default_factory=tuple)
    inventory: tuple[InventoryItem, ...] = field(default_factory=tuple)
    weapons: tuple[Weapon, ...] = field(default_factory=tuple)
    armor: Armor | None = None
    features: tuple[str, ...] = field(default_factory=tuple)
    spells: tuple[str, ...] = field(default_factory=tuple)
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
            character_class=self.character_class,
            race=self.race,
            senses=self.senses,
            initiative_modifier=self.initiative_modifier,
            heroic_inspiration=self.heroic_inspiration,
            proficiency_bonus=self.proficiency_bonus,
            ability_save_dc=self.ability_save_dc,
            walking_speed=self.walking_speed,
            spellcasting_ability=self.spellcasting_ability,
            spell_save_dc=self.spell_save_dc,
            spell_attack_bonus=self.spell_attack_bonus,
            saving_throw_modifiers=dict(self.saving_throw_modifiers),
            skills=self.skills,
            inventory=self.inventory,
            weapons=self.weapons,
            armor=self.armor,
            features=self.features,
            spells=self.spells,
            currency=self.currency,
            resources=dict(self.resources),
            saving_throw_proficiencies=self.saving_throw_proficiencies,
            armor_proficiencies=self.armor_proficiencies,
            weapon_proficiencies=self.weapon_proficiencies,
            tool_proficiencies=self.tool_proficiencies,
            languages=self.languages,
            damage_resistances=self.damage_resistances,
        )
