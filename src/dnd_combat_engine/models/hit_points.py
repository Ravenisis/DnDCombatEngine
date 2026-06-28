"""Hit point model with temporary hit point behavior."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Self


@dataclass(slots=True)
class HitPoints:
    """Current, maximum, and temporary hit points."""

    current: int
    maximum: int
    temporary: int = 0

    def __post_init__(self) -> None:
        """Validate hit point bounds."""
        if self.maximum < 1:
            raise ValueError("maximum hit points must be at least 1")
        if self.current < 0:
            raise ValueError("current hit points cannot be negative")
        if self.temporary < 0:
            raise ValueError("temporary hit points cannot be negative")
        self.current = min(self.current, self.maximum)

    @property
    def is_conscious(self) -> bool:
        """Return whether the creature has at least 1 current hit point."""
        return self.current > 0

    def heal(self, amount: int) -> int:
        """Heal current hit points and return the actual amount restored."""
        if amount < 0:
            raise ValueError("healing amount cannot be negative")
        before = self.current
        self.current = min(self.maximum, self.current + amount)
        return self.current - before

    def apply_damage(self, amount: int) -> int:
        """Apply damage through temporary hit points and return current HP lost."""
        if amount < 0:
            raise ValueError("damage amount cannot be negative")
        absorbed = min(self.temporary, amount)
        self.temporary -= absorbed
        remaining = amount - absorbed
        before = self.current
        self.current = max(0, self.current - remaining)
        return before - self.current

    def grant_temporary(self, amount: int) -> bool:
        """Grant temporary hit points if the amount exceeds the current pool."""
        if amount < 0:
            raise ValueError("temporary hit points cannot be negative")
        if amount > self.temporary:
            self.temporary = amount
            return True
        return False

    def to_dict(self) -> dict[str, int]:
        """Serialize hit points to plain JSON-compatible data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> Self:
        """Build hit points from JSON-compatible data."""
        return cls(**data)

