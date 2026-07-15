"""Compendium controller workflows."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from dnd_combat_engine.models.damage import DamageType
from dnd_combat_engine.models.effects import EffectDefinition
from dnd_combat_engine.models.monsters import Monster
from dnd_combat_engine.models.spells import Spell
from dnd_combat_engine.services.monster_service import MonsterService
from dnd_combat_engine.services.persistence_service import PersistenceService
from dnd_combat_engine.services.spell_service import SpellService


@dataclass(frozen=True, slots=True)
class CompendiumController:
    """UI-facing read workflows for spells and monsters."""

    monster_service: MonsterService
    spell_service: SpellService
    persistence_service: PersistenceService

    def load_spell(self, spell_id: str) -> Spell:
        """Load a spell by id."""
        return self.persistence_service.load_spell(spell_id)

    def class_spell_ids(self, class_id: str, maximum_level: int) -> tuple[str, ...]:
        """Return configured spells available to a class through a spell level."""
        return self.persistence_service.class_spell_ids(class_id, maximum_level)

    def load_action_effect(self, action_id: str) -> EffectDefinition:
        """Load a standalone action effect definition by id."""
        return self.persistence_service.load_action_effect(action_id)

    def action_effects(self) -> tuple[EffectDefinition, ...]:
        """Load all standalone action effect definitions sorted by name."""
        effects = (
            self.load_action_effect(action_id)
            for action_id in self.persistence_service.list_action_effect_ids()
        )
        return tuple(sorted(effects, key=lambda effect: (effect.name.lower(), effect.effect_id)))

    def load_monster(self, monster_id: str) -> Monster:
        """Load a monster by id."""
        return self.persistence_service.load_monster(monster_id)

    def spells_by_level(self, level: int) -> tuple[Spell, ...]:
        """Load all persisted spells for a level."""
        spells = (
            self.load_spell(spell_id) for spell_id in self.persistence_service.list_spell_ids()
        )
        return self.spell_service.by_level(spells, level)

    def monsters_by_challenge(
        self,
        minimum: Fraction | int = 0,
        maximum: Fraction | int | None = None,
    ) -> tuple[Monster, ...]:
        """Load all persisted monsters within a challenge range."""
        monsters = (
            self.load_monster(monster_id)
            for monster_id in self.persistence_service.list_monster_ids()
        )
        return self.monster_service.by_challenge_range(monsters, minimum, maximum)

    def monsters_resistant_to(self, damage_type: DamageType) -> tuple[Monster, ...]:
        """Load monsters resistant or immune to a damage type."""
        monsters = (
            self.load_monster(monster_id)
            for monster_id in self.persistence_service.list_monster_ids()
        )
        return self.monster_service.resistant_to(monsters, damage_type)
