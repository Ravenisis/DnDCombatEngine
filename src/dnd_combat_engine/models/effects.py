"""Targeting and effect resolution models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from dnd_combat_engine.models.action_economy import ActionCost
from dnd_combat_engine.models.rules import RuleSource


class TargetKind(StrEnum):
    """Kinds of combat targets the GUI can select."""

    CHARACTER = "character"
    MONSTER = "monster"


class EffectKind(StrEnum):
    """High-level effect categories resolved by action controls."""

    ATTACK = "attack"
    BUFF = "buff"
    CONDITION = "condition"
    DAMAGE = "damage"
    HEALING = "healing"
    RESOURCE = "resource"
    SAVE = "save"
    UTILITY = "utility"


class TargetProfile(StrEnum):
    """SRD-style targeting shapes for actions and effects."""

    SELF = "self"
    ONE_CREATURE = "one_creature"
    MULTIPLE_CREATURES = "multiple_creatures"
    OBJECT = "object"
    POINT = "point"
    AREA = "area"
    CONE = "cone"
    LINE = "line"
    SPHERE = "sphere"
    CUBE = "cube"
    CYLINDER = "cylinder"
    SPECIAL = "special"


class CheckKind(StrEnum):
    """Kinds of d20 checks a resolvable effect can require."""

    NONE = "none"
    ABILITY_CHECK = "ability_check"
    ATTACK_ROLL = "attack_roll"
    SAVING_THROW = "saving_throw"


class DurationKind(StrEnum):
    """Structured duration categories for rule effects."""

    INSTANTANEOUS = "instantaneous"
    ROUND_BASED = "round_based"
    MINUTE_BASED = "minute_based"
    HOUR_BASED = "hour_based"
    DAY_BASED = "day_based"
    CONCENTRATION = "concentration"
    UNTIL_DISPELLED = "until_dispelled"
    PERMANENT = "permanent"
    SPECIAL = "special"


class InteractionTrigger(StrEnum):
    """Moments when a data-defined effect interaction applies."""

    ON_CAST = "on_cast"
    ON_HIT = "on_hit"
    ON_MISS = "on_miss"
    ON_FAILED_SAVE = "on_failed_save"
    ON_SUCCESSFUL_SAVE = "on_successful_save"
    ON_TARGET = "on_target"
    ON_CHOICE = "on_choice"
    ON_CONSUME = "on_consume"


class InteractionOutcomeKind(StrEnum):
    """Structured outcomes a resolver can apply or explain."""

    APPLY_DAMAGE = "apply_damage"
    APPLY_HEALING = "apply_healing"
    APPLY_BUFF = "apply_buff"
    APPLY_CONDITION = "apply_condition"
    REMOVE_CONDITION = "remove_condition"
    REVIVE = "revive"
    CREATE_LIGHT = "create_light"
    CREATE_CHOICE = "create_choice"
    GRANT_ADVANTAGE = "grant_advantage"
    FORCE_SAVE = "force_save"
    APPLY_ATTACK = "apply_attack"
    NARRATE = "narrate"


@dataclass(frozen=True, slots=True)
class TargetReference:
    """A selected target reference independent of storage details."""

    target_id: str
    name: str
    kind: TargetKind
    source_id: str

    def __post_init__(self) -> None:
        """Validate target reference fields."""
        if not self.target_id:
            raise ValueError("target_id is required")
        if not self.name:
            raise ValueError("name is required")
        if not self.source_id:
            raise ValueError("source_id is required")

    def to_dict(self) -> dict[str, str]:
        """Serialize the target reference to plain JSON-compatible data."""
        return {
            "target_id": self.target_id,
            "name": self.name,
            "kind": self.kind.value,
            "source_id": self.source_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a target reference from JSON-compatible data."""
        return cls(
            target_id=str(data["target_id"]),
            name=str(data["name"]),
            kind=TargetKind(str(data["kind"])),
            source_id=str(data["source_id"]),
        )


@dataclass(frozen=True, slots=True)
class CheckDefinition:
    """A check, attack roll, or saving throw needed by an effect."""

    kind: CheckKind
    ability: str | None = None
    dc: int | None = None
    bonus: int = 0
    proficiency_applies: bool = False

    def __post_init__(self) -> None:
        """Validate check fields."""
        if self.kind != CheckKind.NONE and not self.ability:
            raise ValueError("ability is required for checks")
        if self.dc is not None and self.dc < 1:
            raise ValueError("dc must be at least 1")

    def to_dict(self) -> dict[str, object]:
        """Serialize the check definition to JSON-compatible data."""
        return {
            "kind": self.kind.value,
            "ability": self.ability,
            "dc": self.dc,
            "bonus": self.bonus,
            "proficiency_applies": self.proficiency_applies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a check definition from JSON-compatible data."""
        dc = data.get("dc")
        return cls(
            kind=CheckKind(str(data.get("kind", CheckKind.NONE.value))),
            ability=str(data["ability"]) if data.get("ability") is not None else None,
            dc=int(dc) if dc is not None else None,
            bonus=int(data.get("bonus", 0)),
            proficiency_applies=bool(data.get("proficiency_applies", False)),
        )


@dataclass(frozen=True, slots=True)
class DurationProfile:
    """Structured duration information for an effect."""

    kind: DurationKind
    amount: int | None = None
    text: str = ""

    def __post_init__(self) -> None:
        """Validate duration amount."""
        if self.amount is not None and self.amount < 1:
            raise ValueError("duration amount must be at least 1")

    def to_dict(self) -> dict[str, object]:
        """Serialize duration information to JSON-compatible data."""
        return {
            "kind": self.kind.value,
            "amount": self.amount,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build duration information from JSON-compatible data."""
        amount = data.get("amount")
        return cls(
            kind=DurationKind(str(data["kind"])),
            amount=int(amount) if amount is not None else None,
            text=str(data.get("text", "")),
        )


@dataclass(frozen=True, slots=True)
class EffectInteraction:
    """A data-backed rule outcome attached to an effect definition."""

    interaction_id: str
    trigger: InteractionTrigger
    outcome_kind: InteractionOutcomeKind
    label: str = ""
    value: str | None = None
    scaling: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate interaction identity and value."""
        if not self.interaction_id:
            raise ValueError("interaction_id is required")
        if self.value is not None and not self.value:
            raise ValueError("interaction value cannot be blank")

    def summary(self) -> str:
        """Return a compact rules summary for combat log detail."""
        trigger = self.trigger.value.replace("_", " ")
        kind = self.outcome_kind.value.replace("_", " ")
        label = f" {self.label}" if self.label else ""
        value = f" {self.value}" if self.value else ""
        scaling = _scaling_summary(self.scaling)
        return f"{trigger}: {kind}{label}{value}{scaling}."

    def to_dict(self) -> dict[str, object]:
        """Serialize the interaction to JSON-compatible data."""
        return {
            "interaction_id": self.interaction_id,
            "trigger": self.trigger.value,
            "outcome_kind": self.outcome_kind.value,
            "label": self.label,
            "value": self.value,
            "scaling": dict(self.scaling),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build an effect interaction from JSON-compatible data."""
        return cls(
            interaction_id=str(data["interaction_id"]),
            trigger=InteractionTrigger(str(data["trigger"])),
            outcome_kind=InteractionOutcomeKind(str(data["outcome_kind"])),
            label=str(data.get("label", "")),
            value=str(data["value"]) if data.get("value") is not None else None,
            scaling=_dict_from_data(data.get("scaling")),
            metadata=_dict_from_data(data.get("metadata")),
        )


@dataclass(frozen=True, slots=True)
class EffectDefinition:
    """A rule-defined effect before it is resolved against targets."""

    effect_id: str
    name: str
    effect_kind: EffectKind
    target_profile: TargetProfile
    action_cost: ActionCost = ActionCost.ACTION
    range_text: str = ""
    duration: DurationProfile = field(
        default_factory=lambda: DurationProfile(DurationKind.INSTANTANEOUS)
    )
    check: CheckDefinition = field(default_factory=lambda: CheckDefinition(CheckKind.NONE))
    resource_cost: str | None = None
    dice: str | None = None
    interactions: tuple[EffectInteraction, ...] = field(default_factory=tuple)
    rule_source: RuleSource | None = None

    def __post_init__(self) -> None:
        """Validate effect identity and dice."""
        if not self.effect_id:
            raise ValueError("effect_id is required")
        if not self.name:
            raise ValueError("effect name is required")
        if self.dice is not None and not self.dice:
            raise ValueError("dice cannot be blank")

    @property
    def requires_target(self) -> bool:
        """Return whether this effect needs a target selection."""
        return self.target_profile not in {TargetProfile.SELF, TargetProfile.SPECIAL}

    @property
    def starts_concentration(self) -> bool:
        """Return whether resolving this effect starts concentration."""
        return self.duration.kind == DurationKind.CONCENTRATION

    def to_dict(self) -> dict[str, object]:
        """Serialize the effect definition to JSON-compatible data."""
        return {
            "effect_id": self.effect_id,
            "name": self.name,
            "effect_kind": self.effect_kind.value,
            "target_profile": self.target_profile.value,
            "action_cost": self.action_cost.value,
            "range_text": self.range_text,
            "duration": self.duration.to_dict(),
            "check": self.check.to_dict(),
            "resource_cost": self.resource_cost,
            "dice": self.dice,
            "interactions": [interaction.to_dict() for interaction in self.interactions],
            "rule_source": self.rule_source.to_dict() if self.rule_source else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build an effect definition from JSON-compatible data."""
        return cls(
            effect_id=str(data["effect_id"]),
            name=str(data["name"]),
            effect_kind=EffectKind(str(data["effect_kind"])),
            target_profile=TargetProfile(str(data["target_profile"])),
            action_cost=ActionCost(str(data.get("action_cost", ActionCost.ACTION.value))),
            range_text=str(data.get("range_text", "")),
            duration=_duration_from_data(data.get("duration")),
            check=_check_from_data(data.get("check")),
            resource_cost=(
                str(data["resource_cost"]) if data.get("resource_cost") is not None else None
            ),
            dice=str(data["dice"]) if data.get("dice") is not None else None,
            interactions=tuple(
                EffectInteraction.from_dict(interaction)
                for interaction in data.get("interactions", [])
                if isinstance(interaction, dict)
            ),
            rule_source=_rule_source_from_data(data.get("rule_source")),
        )


@dataclass(frozen=True, slots=True)
class EffectResolution:
    """A resolved effect summary for combat workspace logging."""

    source_name: str
    effect_name: str
    effect_kind: EffectKind
    target: TargetReference | None = None
    total: int | None = None
    detail: str = ""

    def message(self) -> str:
        """Return a compact player-facing resolution message."""
        target_text = f" on {self.target.name}" if self.target is not None else ""
        total_text = "" if self.total is None else f" Total {self.total}."
        detail_text = "" if not self.detail else f" {self.detail}"
        return (
            f"{self.source_name} resolves {self.effect_name}"
            f"{target_text} [{self.effect_kind.value}].{total_text}{detail_text}"
        )


def _check_from_data(data: object) -> CheckDefinition:
    if isinstance(data, dict):
        return CheckDefinition.from_dict(data)
    return CheckDefinition(CheckKind.NONE)


def _duration_from_data(data: object) -> DurationProfile:
    if isinstance(data, dict):
        return DurationProfile.from_dict(data)
    return DurationProfile(DurationKind.INSTANTANEOUS)


def _rule_source_from_data(data: object) -> RuleSource | None:
    if isinstance(data, dict):
        return RuleSource.from_dict(data)
    return None


def _dict_from_data(data: object) -> dict[str, object]:
    if isinstance(data, dict):
        return dict(data)
    return {}


def _scaling_summary(scaling: dict[str, object]) -> str:
    if not scaling:
        return ""
    mode = scaling.get("mode")
    per_level = scaling.get("per_slot_level_above_base")
    if mode == "spell_slot" and per_level:
        base = scaling.get("base_spell_level")
        base_text = f" above level {base}" if base is not None else ""
        return f" (scales {per_level}{base_text})"
    if mode:
        return f" (scales by {mode})"
    return ""
