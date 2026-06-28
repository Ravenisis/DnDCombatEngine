"""Resource pool models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(slots=True)
class ResourcePool:
    """A spendable character resource such as spell slots, ki, or rage uses."""

    name: str
    current: int
    maximum: int

    def __post_init__(self) -> None:
        """Validate resource bounds."""
        if not self.name:
            raise ValueError("resource name is required")
        if self.maximum < 0:
            raise ValueError("maximum resource value cannot be negative")
        if self.current < 0:
            raise ValueError("current resource value cannot be negative")
        self.current = min(self.current, self.maximum)

    def expend(self, amount: int = 1) -> bool:
        """Spend a resource amount if available."""
        if amount < 1:
            raise ValueError("expend amount must be at least 1")
        if self.current < amount:
            return False
        self.current -= amount
        return True

    def restore(self, amount: int) -> int:
        """Restore a resource amount and return the actual amount restored."""
        if amount < 0:
            raise ValueError("restore amount cannot be negative")
        before = self.current
        self.current = min(self.maximum, self.current + amount)
        return self.current - before

    def reset(self) -> None:
        """Restore the pool to its maximum value."""
        self.current = self.maximum

    def to_dict(self) -> dict[str, object]:
        """Serialize the resource pool to plain JSON-compatible data."""
        return {"name": self.name, "current": self.current, "maximum": self.maximum}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a resource pool from JSON-compatible data."""
        return cls(
            name=str(data["name"]),
            current=int(data["current"]),
            maximum=int(data["maximum"]),
        )

