"""Visual polyhedral dice controls for the action bar."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

DICE_OPTIONS = (4, 6, 8, 10, 12, 20, 100)


class DiceBarWidget:
    """Factory for the visual dice row above the quick action bar."""

    @staticmethod
    def create(qt, on_roll: Callable[[str], object] | None = None):
        """Create buttons for the standard seven-piece polyhedral dice set."""
        widget = qt.QtWidgets.QWidget()
        if hasattr(widget, "setObjectName"):
            widget.setObjectName("PolyhedralDiceBar")
        layout = qt.QtWidgets.QHBoxLayout(widget)
        if hasattr(layout, "setAlignment"):
            layout.setAlignment(qt.QtCore.Qt.AlignmentFlag.AlignCenter)
        if hasattr(layout, "setContentsMargins"):
            layout.setContentsMargins(4, 2, 4, 2)
        if hasattr(layout, "setSpacing"):
            layout.setSpacing(8)

        for sides in DICE_OPTIONS:
            layout.addWidget(_die_button(qt, sides, on_roll))
        return widget


def _die_button(qt, sides: int, on_roll: Callable[[str], object] | None):
    button_class = getattr(qt.QtWidgets, "QToolButton", qt.QtWidgets.QPushButton)
    button = button_class()
    notation = f"1d{sides}"
    label = "d%" if sides == 100 else f"d{sides}"
    button.setText(label)
    if hasattr(button, "setObjectName"):
        button.setObjectName(f"DiceRollButton_d{sides}")
    button.setToolTip(f"Roll {label} in the Combat Workspace")
    if hasattr(button, "setFixedSize"):
        button.setFixedSize(60, 58)

    icon_path = _icon_path(sides)
    icon_class = getattr(qt.QtGui, "QIcon", None)
    if icon_class is not None and icon_path.exists() and hasattr(button, "setIcon"):
        button.setIcon(icon_class(str(icon_path)))
        size_class = getattr(qt.QtCore, "QSize", None)
        if size_class is not None and hasattr(button, "setIconSize"):
            button.setIconSize(size_class(34, 34))

    style = _text_under_icon_style(qt)
    if style is not None and hasattr(button, "setToolButtonStyle"):
        button.setToolButtonStyle(style)
    button.clicked.connect(
        lambda checked=False, die_notation=notation: _roll(on_roll, die_notation)
    )
    return button


def _roll(on_roll: Callable[[str], object] | None, notation: str) -> None:
    if on_roll is not None:
        on_roll(notation)


def _icon_path(sides: int) -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "dice_icons" / f"d{sides}.svg"


def _text_under_icon_style(qt):
    style_group = getattr(qt.QtCore.Qt, "ToolButtonStyle", qt.QtCore.Qt)
    return getattr(style_group, "ToolButtonTextUnderIcon", None)
