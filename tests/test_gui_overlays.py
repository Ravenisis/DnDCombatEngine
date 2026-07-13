"""Tests for in-window GUI overlays used by streamed sessions."""

from __future__ import annotations

from types import SimpleNamespace

from dnd_combat_engine.gui.overlays import create_embedded_popup, show_embedded_popup


def test_embedded_popup_is_a_child_and_centers_over_its_parent() -> None:
    """Application panels remain inside the captured main window surface."""

    class Parent:
        def width(self) -> int:
            return 1_200

        def height(self) -> int:
            return 800

    class Popup:
        def __init__(self, parent) -> None:
            self.parent = parent
            self.object_name = ""
            self.position = None
            self.shown = False
            self.raised = False
            self.activated = False

        def setObjectName(self, name: str) -> None:  # noqa: N802
            self.object_name = name

        def width(self) -> int:
            return 360

        def height(self) -> int:
            return 520

        def move(self, x: int, y: int) -> None:
            self.position = (x, y)

        def show(self) -> None:
            self.shown = True

        def raise_(self) -> None:
            self.raised = True

        def activateWindow(self) -> None:  # noqa: N802
            self.activated = True

    parent = Parent()
    qt = SimpleNamespace(QtWidgets=SimpleNamespace(QFrame=Popup))

    popup = create_embedded_popup(qt, parent)
    assert popup is not None
    show_embedded_popup(parent, popup)

    assert popup.parent is parent
    assert popup.object_name == "EmbeddedPopup"
    assert popup.position == (420, 140)
    assert popup.shown and popup.raised and popup.activated
