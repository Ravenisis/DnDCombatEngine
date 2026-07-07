"""Turn action economy models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class ActionCost(StrEnum):
    """Action economy costs a combat option can consume."""

    ACTION = "action"
    BONUS_ACTION = "bonus_action"
    REACTION = "reaction"
    MOVEMENT = "movement"
    OBJECT_INTERACTION = "object_interaction"
    FREE = "free"
    SPECIAL = "special"


@dataclass(slots=True)
class TurnEconomy:
    """Track the action economy spent by one combatant during a turn."""

    action_used: bool = False
    bonus_action_used: bool = False
    reaction_used: bool = False
    object_interaction_used: bool = False
    movement_spent: int = 0
    movement_maximum: int = 30

    def __post_init__(self) -> None:
        """Validate movement bounds."""
        if self.movement_maximum < 0:
            raise ValueError("movement maximum cannot be negative")
        if self.movement_spent < 0:
            raise ValueError("movement spent cannot be negative")
        if self.movement_spent > self.movement_maximum:
            raise ValueError("movement spent cannot exceed movement maximum")

    def can_spend(self, cost: ActionCost, amount: int = 0) -> bool:
        """Return whether a cost can be paid from this turn economy."""
        if cost == ActionCost.ACTION:
            return not self.action_used
        if cost == ActionCost.BONUS_ACTION:
            return not self.bonus_action_used
        if cost == ActionCost.REACTION:
            return not self.reaction_used
        if cost == ActionCost.OBJECT_INTERACTION:
            return not self.object_interaction_used
        if cost == ActionCost.MOVEMENT:
            if amount < 0:
                raise ValueError("movement amount cannot be negative")
            return self.movement_spent + amount <= self.movement_maximum
        return True

    def spend(self, cost: ActionCost, amount: int = 0) -> bool:
        """Spend an action economy cost if it is available."""
        if not self.can_spend(cost, amount):
            return False
        if cost == ActionCost.ACTION:
            self.action_used = True
        elif cost == ActionCost.BONUS_ACTION:
            self.bonus_action_used = True
        elif cost == ActionCost.REACTION:
            self.reaction_used = True
        elif cost == ActionCost.OBJECT_INTERACTION:
            self.object_interaction_used = True
        elif cost == ActionCost.MOVEMENT:
            self.movement_spent += amount
        return True

    def reset_turn(self) -> None:
        """Reset per-turn action and movement use."""
        self.action_used = False
        self.bonus_action_used = False
        self.object_interaction_used = False
        self.movement_spent = 0

    def reset_reaction(self) -> None:
        """Restore the reaction at the start of a combatant's turn."""
        self.reaction_used = False

    def to_dict(self) -> dict[str, object]:
        """Serialize turn economy state to JSON-compatible data."""
        return {
            "action_used": self.action_used,
            "bonus_action_used": self.bonus_action_used,
            "reaction_used": self.reaction_used,
            "object_interaction_used": self.object_interaction_used,
            "movement_spent": self.movement_spent,
            "movement_maximum": self.movement_maximum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build turn economy state from JSON-compatible data."""
        return cls(
            action_used=bool(data.get("action_used", False)),
            bonus_action_used=bool(data.get("bonus_action_used", False)),
            reaction_used=bool(data.get("reaction_used", False)),
            object_interaction_used=bool(data.get("object_interaction_used", False)),
            movement_spent=int(data.get("movement_spent", 0)),
            movement_maximum=int(data.get("movement_maximum", 30)),
        )

