"""GUI action specifications."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuiActionSpec:
    """Declarative GUI action metadata."""

    action_id: str
    menu: str
    text: str
    status_tip: str
    shortcut: str | None = None

    def __post_init__(self) -> None:
        """Validate action metadata."""
        if not self.action_id:
            raise ValueError("action_id is required")
        if not self.menu:
            raise ValueError("menu is required")
        if not self.text:
            raise ValueError("text is required")
        if not self.status_tip:
            raise ValueError("status_tip is required")


def default_action_specs() -> tuple[GuiActionSpec, ...]:
    """Return default GUI action specifications."""
    return (
        GuiActionSpec("file.exit", "File", "Exit", "Close the application", "Ctrl+Q"),
        GuiActionSpec("view.reset_layout", "View", "Reset Layout", "Restore dock layout"),
        GuiActionSpec("combat.quick_attack", "Combat", "Quick Attack", "Run a sample attack"),
        GuiActionSpec("dice.roll_d20", "Dice", "Roll d20", "Roll a d20", "Ctrl+R"),
    )


def action_specs_by_menu(specs: tuple[GuiActionSpec, ...]) -> dict[str, tuple[GuiActionSpec, ...]]:
    """Group action specifications by menu name."""
    grouped: dict[str, list[GuiActionSpec]] = {}
    for spec in specs:
        grouped.setdefault(spec.menu, []).append(spec)
    return {menu: tuple(items) for menu, items in grouped.items()}

