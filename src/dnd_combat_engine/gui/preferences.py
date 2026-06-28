"""GUI preference models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class GuiPreferences:
    """User-configurable GUI preferences."""

    dark_mode: bool = True
    auto_save: bool = True
    confirm_exit: bool = True
    default_dice: str = "1d20"

    def __post_init__(self) -> None:
        """Validate preference values."""
        if not self.default_dice:
            raise ValueError("default_dice is required")

    def to_dict(self) -> dict[str, object]:
        """Serialize preferences to plain JSON-compatible data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build preferences from JSON-compatible data."""
        return cls(
            dark_mode=bool(data.get("dark_mode", True)),
            auto_save=bool(data.get("auto_save", True)),
            confirm_exit=bool(data.get("confirm_exit", True)),
            default_dice=str(data.get("default_dice", "1d20")),
        )
