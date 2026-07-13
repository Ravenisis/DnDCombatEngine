"""Helpers for dialogs that remain inside the main application window."""

from __future__ import annotations

from typing import Any


def create_embedded_popup(qt: Any, parent: Any) -> Any | None:
    """Create a true child overlay for panels shown during a window-only stream."""
    widget_class = (
        getattr(qt.QtWidgets, "QFrame", None)
        or getattr(qt.QtWidgets, "QWidget", None)
        or getattr(qt.QtWidgets, "QDialog", None)
    )
    if widget_class is None:
        return None
    try:
        popup = widget_class(parent)
    except TypeError:
        popup = widget_class()
    if hasattr(popup, "setObjectName"):
        popup.setObjectName("EmbeddedPopup")
    return popup


def create_embedded_dialog(qt: Any, parent: Any) -> Any | None:
    """Create a parented modal dialog where an interaction requires acceptance."""
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    if dialog_class is None:
        return None
    try:
        return dialog_class(parent)
    except TypeError:
        return dialog_class()


def show_embedded_popup(parent: Any, popup: Any) -> None:
    """Show a child popup centered over its parent application surface."""
    _center_over_parent(parent, popup)
    if hasattr(popup, "show"):
        popup.show()
    if hasattr(popup, "raise_"):
        popup.raise_()
    if hasattr(popup, "activateWindow"):
        popup.activateWindow()


def _center_over_parent(parent: Any, popup: Any) -> None:
    if not hasattr(popup, "move"):
        return
    parent_width = _dimension(parent, "width")
    parent_height = _dimension(parent, "height")
    popup_width = _dimension(popup, "width")
    popup_height = _dimension(popup, "height")
    if min(parent_width, parent_height, popup_width, popup_height) <= 0:
        return
    popup.move(
        max(0, (parent_width - popup_width) // 2),
        max(0, (parent_height - popup_height) // 2),
    )


def _dimension(widget: Any, name: str) -> int:
    value = getattr(widget, name, None)
    return int(value()) if callable(value) else 0
