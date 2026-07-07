"""Domain models for characters, equipment, and combat state."""

from dnd_combat_engine.models.abilities import AbilityScores
from dnd_combat_engine.models.action_bar import ActionBar, ActionBarActionKind, ActionBarButton
from dnd_combat_engine.models.action_economy import ActionCost, TurnEconomy
from dnd_combat_engine.models.campaigns import Campaign, CampaignActivityEntry, CampaignStatus
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.combat_log import CombatLog, CombatLogEntry, CombatLogEntryType
from dnd_combat_engine.models.concentration import (
    ConcentrationOutcome,
    ConcentrationResult,
    ConcentrationState,
    concentration_save_dc,
)
from dnd_combat_engine.models.conditions import Condition, ConditionName
from dnd_combat_engine.models.currency import CurrencyPurse
from dnd_combat_engine.models.damage import DamageComponent, DamageProfile, DamageType
from dnd_combat_engine.models.effects import (
    CheckDefinition,
    CheckKind,
    DurationKind,
    DurationProfile,
    EffectDefinition,
    EffectKind,
    EffectResolution,
    TargetKind,
    TargetProfile,
    TargetReference,
)
from dnd_combat_engine.models.encounters import (
    Encounter,
    EncounterParticipant,
    EncounterStatus,
    ParticipantKind,
)
from dnd_combat_engine.models.equipment import Armor, Weapon
from dnd_combat_engine.models.hit_points import HitPoints
from dnd_combat_engine.models.imports import CharacterImportDraft
from dnd_combat_engine.models.inventory import InventoryItem, ItemCategory
from dnd_combat_engine.models.monsters import CreatureSize, CreatureType, Monster
from dnd_combat_engine.models.resources import ResourcePool
from dnd_combat_engine.models.rules import RuleSource
from dnd_combat_engine.models.spell_slots import (
    ensure_spell_slot_resources,
    inferred_spell_slots,
)
from dnd_combat_engine.models.spells import Spell, SpellSchool

__all__ = [
    "AbilityScores",
    "ActionBar",
    "ActionBarActionKind",
    "ActionBarButton",
    "ActionCost",
    "Armor",
    "Campaign",
    "CampaignActivityEntry",
    "CampaignStatus",
    "Character",
    "CharacterImportDraft",
    "CheckDefinition",
    "CheckKind",
    "CombatLog",
    "CombatLogEntry",
    "CombatLogEntryType",
    "Condition",
    "ConditionName",
    "ConcentrationOutcome",
    "ConcentrationResult",
    "ConcentrationState",
    "CreatureSize",
    "CreatureType",
    "CurrencyPurse",
    "DamageComponent",
    "DamageProfile",
    "DamageType",
    "DurationKind",
    "DurationProfile",
    "EffectDefinition",
    "EffectKind",
    "EffectResolution",
    "Encounter",
    "EncounterParticipant",
    "EncounterStatus",
    "HitPoints",
    "InventoryItem",
    "ItemCategory",
    "Monster",
    "ParticipantKind",
    "ResourcePool",
    "RuleSource",
    "Spell",
    "SpellSchool",
    "TargetProfile",
    "TargetKind",
    "TargetReference",
    "TurnEconomy",
    "Weapon",
    "concentration_save_dc",
    "ensure_spell_slot_resources",
    "inferred_spell_slots",
]
