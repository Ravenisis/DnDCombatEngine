"""Tests for in-window GUI overlays used by streamed sessions."""

from __future__ import annotations

from types import SimpleNamespace

from dnd_combat_engine.gui.overlays import (
    create_embedded_dialog,
    create_embedded_popup,
    create_tool_popup,
    show_embedded_popup,
    show_tool_popup,
)


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


def test_embedded_popup_closes_with_escape() -> None:
    class Popup:
        def __init__(self, parent) -> None:
            self.parent = parent

        def close(self) -> None:
            self.closed = True

    class Event:
        def key(self) -> int:
            return 27

        def accept(self) -> None:
            self.accepted = True

    qt = SimpleNamespace(
        QtCore=SimpleNamespace(
            Qt=SimpleNamespace(Key=SimpleNamespace(Key_Escape=27))
        ),
        QtWidgets=SimpleNamespace(QFrame=Popup),
    )
    popup = create_embedded_popup(qt, object())
    assert popup is not None
    event = Event()

    popup.keyPressEvent(event)

    assert popup.closed is True
    assert event.accepted is True


def test_embedded_dialog_rejects_with_escape() -> None:
    class Dialog:
        def __init__(self, parent=None) -> None:
            self.parent = parent

        def reject(self) -> None:
            self.rejected = True

    class Event:
        def key(self) -> int:
            return 27

        def accept(self) -> None:
            self.accepted = True

    qt = SimpleNamespace(
        QtCore=SimpleNamespace(Qt=SimpleNamespace(Key=SimpleNamespace(Key_Escape=27))),
        QtWidgets=SimpleNamespace(QDialog=Dialog),
    )
    dialog = create_embedded_dialog(qt, object())
    event = Event()

    dialog.keyPressEvent(event)

    assert dialog.rejected is True
    assert event.accepted is True


def test_tool_popup_restores_and_saves_persistent_geometry() -> None:
    class Settings:
        values = {"tool_windows/inventory/geometry": b"remembered"}

        def __init__(self, organization, application) -> None:
            self.identity = (organization, application)

        def value(self, key):
            return self.values.get(key)

        def setValue(self, key, value) -> None:  # noqa: N802
            self.values[key] = value

        def sync(self) -> None:
            self.synced = True

    class Dialog:
        def __init__(self, parent=None, flags=None) -> None:
            self.parent = parent
            self.flags = flags
            self.position = None
            self.shown = False

        def setObjectName(self, name: str) -> None:  # noqa: N802
            self.object_name = name

        def restoreGeometry(self, value) -> bool:  # noqa: N802
            self.restored = value
            return True

        def saveGeometry(self):  # noqa: N802
            return b"latest"

        def show(self) -> None:
            self.shown = True

        def raise_(self) -> None:
            self.raised = True

        def activateWindow(self) -> None:  # noqa: N802
            self.activated = True

    window_type = SimpleNamespace(
        SubWindow=1,
        WindowTitleHint=2,
        WindowSystemMenuHint=4,
        WindowCloseButtonHint=8,
    )
    qt = SimpleNamespace(
        QtCore=SimpleNamespace(QSettings=Settings, Qt=SimpleNamespace(WindowType=window_type)),
        QtWidgets=SimpleNamespace(QDialog=Dialog),
    )
    popup = create_tool_popup(qt, object(), "inventory")
    popup._dnd_native_close_callback = lambda: setattr(popup, "unregistered", True)

    show_tool_popup(object(), popup)
    popup.closeEvent(object())

    assert popup.object_name == "ToolWindow_inventory"
    assert popup.flags == 15
    assert popup.restored == b"remembered"
    assert popup.position is None
    assert popup.shown and popup.raised and popup.activated
    assert popup.unregistered is True
    assert Settings.values["tool_windows/inventory/geometry"] == b"latest"
