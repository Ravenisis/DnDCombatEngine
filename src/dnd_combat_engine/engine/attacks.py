"""Attack workflow data objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.damage import DamageComponent, DamageType
from dnd_combat_engine.models.equipment import Weapon
from dnd_combat_engine.utils.dice import DiceRollResult


@dataclass(frozen=True, slots=True)
class AttackRequest:
    """A request to resolve one weapon attack."""

    attacker: Character
    target: Character
    weapon: Weapon
    target_armor_class: int
    attack_bonus: int = 0
    damage_bonus: int = 0
    critical_threshold: int = 20
    attack_bonus_dice: tuple[str, ...] = field(default_factory=tuple)
    extra_damage: tuple[DamageComponent, ...] = field(default_factory=tuple)
    active_features: tuple[str, ...] = field(default_factory=tuple)
    advantage: bool = False
    disadvantage: bool = False

    def __post_init__(self) -> None:
        """Validate attack request values."""
        if self.target_armor_class < 1:
            raise ValueError("target armor class must be at least 1")
        if not 2 <= self.critical_threshold <= 20:
            raise ValueError("critical threshold must be between 2 and 20")

    @property
    def attack_dice(self) -> str:
        """Return the d20 expression used for this attack roll."""
        if self.advantage and not self.disadvantage:
            return "2d20kh1"
        if self.disadvantage and not self.advantage:
            return "2d20kl1"
        return "1d20"


@dataclass(frozen=True, slots=True)
class DamageRoll:
    """A typed damage roll result."""

    damage_type: DamageType
    roll: DiceRollResult

    @property
    def total(self) -> int:
        """Return this component's total damage."""
        return self.roll.total


@dataclass(frozen=True, slots=True)
class AttackResult:
    """The result of resolving one attack."""

    request: AttackRequest
    attack_roll: DiceRollResult
    attack_total: int
    hit: bool
    critical: bool
    attack_bonus_rolls: tuple[DiceRollResult, ...] = field(default_factory=tuple)
    damage_rolls: tuple[DamageRoll, ...] = field(default_factory=tuple)
    damage_bonus: int = 0
    damage_applied: int = 0

    @property
    def natural_roll(self) -> int:
        """Return the kept natural d20 value."""
        return max(self.attack_roll.kept)

    @property
    def damage_total(self) -> int:
        """Return total damage before target mitigation rules."""
        return sum(damage.total for damage in self.damage_rolls) + self.damage_bonus

    @property
    def damage_by_type(self) -> dict[DamageType, int]:
        """Return damage totals grouped by damage type."""
        totals: dict[DamageType, int] = {}
        for damage in self.damage_rolls:
            totals[damage.damage_type] = totals.get(damage.damage_type, 0) + damage.total
        return totals
