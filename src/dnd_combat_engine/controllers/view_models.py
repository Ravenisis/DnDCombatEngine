"""UI-facing view models."""

from __future__ import annotations

from dataclasses import dataclass

from dnd_combat_engine.engine.attacks import AttackResult
from dnd_combat_engine.engine.initiative import InitiativeTracker
from dnd_combat_engine.models.campaigns import Campaign
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.encounters import Encounter


@dataclass(frozen=True, slots=True)
class CharacterSummary:
    """Compact character state for UI lists."""

    character_id: str
    name: str
    current_hp: int
    maximum_hp: int
    temporary_hp: int
    armor_class: int | None = None

    @classmethod
    def from_character(cls, character: Character) -> CharacterSummary:
        """Build a character summary."""
        return cls(
            character_id=character.character_id,
            name=character.name,
            current_hp=character.hit_points.current,
            maximum_hp=character.hit_points.maximum,
            temporary_hp=character.hit_points.temporary,
            armor_class=character.armor.armor_class if character.armor else None,
        )


@dataclass(frozen=True, slots=True)
class CampaignSummary:
    """Compact campaign state for UI lists."""

    campaign_id: str
    name: str
    status: str
    character_count: int
    encounter_count: int

    @classmethod
    def from_campaign(cls, campaign: Campaign) -> CampaignSummary:
        """Build a campaign summary."""
        return cls(
            campaign_id=campaign.campaign_id,
            name=campaign.name,
            status=campaign.status.value,
            character_count=len(campaign.character_ids),
            encounter_count=len(campaign.encounter_ids),
        )


@dataclass(frozen=True, slots=True)
class AttackSummary:
    """Compact attack result for UI display."""

    attacker: str
    target: str
    weapon: str
    attack_total: int
    hit: bool
    critical: bool
    critical_miss: bool
    damage_total: int
    damage_applied: int

    @classmethod
    def from_result(cls, result: AttackResult) -> AttackSummary:
        """Build an attack summary from an attack result."""
        return cls(
            attacker=result.request.attacker.name,
            target=result.request.target.name,
            weapon=result.request.weapon.name,
            attack_total=result.attack_total,
            hit=result.hit,
            critical=result.critical,
            critical_miss=result.critical_miss,
            damage_total=result.damage_total,
            damage_applied=result.damage_applied,
        )


@dataclass(frozen=True, slots=True)
class EncounterSummary:
    """Compact encounter state for UI lists."""

    encounter_id: str
    name: str
    status: str
    participant_count: int
    round_number: int

    @classmethod
    def from_encounter(cls, encounter: Encounter) -> EncounterSummary:
        """Build an encounter summary."""
        return cls(
            encounter_id=encounter.encounter_id,
            name=encounter.name,
            status=encounter.status.value,
            participant_count=sum(participant.quantity for participant in encounter.participants),
            round_number=encounter.round_number,
        )


@dataclass(frozen=True, slots=True)
class InitiativeSummary:
    """Compact initiative tracker state for UI display."""

    round_number: int
    active_combatant: str | None
    order: tuple[str, ...]

    @classmethod
    def from_tracker(cls, tracker: InitiativeTracker) -> InitiativeSummary:
        """Build an initiative summary."""
        current = tracker.current
        return cls(
            round_number=tracker.round_number,
            active_combatant=current.combatant.name if current else None,
            order=tuple(entry.combatant.name for entry in tracker.entries),
        )
