"""Helpers for dialogs that remain inside the main application window."""

from __future__ import annotations

from typing import Any

SETTINGS_ORGANIZATION = "Ravenisis"
SETTINGS_APPLICATION = "DnDCombatEngine"


def create_embedded_popup(qt: Any, parent: Any) -> Any | None:
    """Create a true child overlay for panels shown during a window-only stream."""
    widget_class = (
        getattr(qt.QtWidgets, "QFrame", None)
        or getattr(qt.QtWidgets, "QWidget", None)
        or getattr(qt.QtWidgets, "QDialog", None)
    )
    if widget_class is None:
        return None

    class EscapeClosablePopup(widget_class):
        def keyPressEvent(self, event: Any) -> None:  # noqa: N802
            if _is_escape_event(qt, event):
                callback = getattr(self, "_dnd_escape_callback", None)
                if callable(callback):
                    callback()
                elif hasattr(self, "close"):
                    self.close()
                if hasattr(event, "accept"):
                    event.accept()
                return
            handler = getattr(super(), "keyPressEvent", None)
            if callable(handler):
                handler(event)

    try:
        popup = EscapeClosablePopup(parent)
    except TypeError:
        popup = EscapeClosablePopup()
    if hasattr(popup, "setObjectName"):
        popup.setObjectName("EmbeddedPopup")
    return popup


def create_embedded_dialog(qt: Any, parent: Any) -> Any | None:
    """Create a parented modal dialog where an interaction requires acceptance."""
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    if dialog_class is None:
        return None


    class EscapeClosableDialog(dialog_class):
        def keyPressEvent(self, event: Any) -> None:  # noqa: N802
            if _is_escape_event(qt, event):
                if hasattr(self, "reject"):
                    self.reject()
                elif hasattr(self, "close"):
                    self.close()
                if hasattr(event, "accept"):
                    event.accept()
                return
            handler = getattr(super(), "keyPressEvent", None)
            if callable(handler):
                handler(event)

    try:
        return EscapeClosableDialog(parent)
    except TypeError:
        return EscapeClosableDialog()


def create_tool_popup(qt: Any, parent: Any, key: str) -> Any | None:
    """Create a movable child tool window with persistent geometry and close controls."""
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    if dialog_class is None:
        popup = create_embedded_popup(qt, parent)
        if popup is not None:
            popup._dnd_tool_window = True
            popup._dnd_geometry_restored = False
        return popup

    class PersistentToolWindow(dialog_class):
        def keyPressEvent(self, event: Any) -> None:  # noqa: N802
            if _is_escape_event(qt, event):
                child_popup = _top_visible_child_popup(self)
                if child_popup is not None:
                    child_popup.close()
                    if hasattr(event, "accept"):
                        event.accept()
                    return
                callback = getattr(self, "_dnd_escape_callback", None)
                if callable(callback):
                    callback()
                elif hasattr(self, "close"):
                    self.close()
                if hasattr(event, "accept"):
                    event.accept()
                return
            handler = getattr(super(), "keyPressEvent", None)
            if callable(handler):
                handler(event)

        def closeEvent(self, event: Any) -> None:  # noqa: N802
            _save_tool_geometry(qt, self, key)
            callback = getattr(self, "_dnd_native_close_callback", None)
            if callable(callback):
                callback()
            handler = getattr(super(), "closeEvent", None)
            if callable(handler):
                handler(event)

    flags = _tool_window_flags(qt)
    try:
        popup = (
            PersistentToolWindow(parent, flags)
            if flags is not None
            else PersistentToolWindow(parent)
        )
    except TypeError:
        try:
            popup = PersistentToolWindow(parent)
        except TypeError:
            popup = PersistentToolWindow()
    if hasattr(popup, "setObjectName"):
        popup.setObjectName(f"ToolWindow_{key}")
    popup._dnd_tool_window = True
    popup._dnd_tool_qt = qt
    popup._dnd_tool_key = key
    popup._dnd_geometry_restored = False
    popup._dnd_geometry_restore_attempted = False
    return popup


def _top_visible_child_popup(widget: Any) -> Any | None:
    """Return the most recently opened visible child overlay."""
    popups = getattr(widget, "_dnd_child_popups", ())
    for popup in reversed(popups):
        is_visible = getattr(popup, "isVisible", None)
        if not callable(is_visible) or is_visible():
            return popup
    return None


def show_embedded_popup(parent: Any, popup: Any) -> None:
    """Show a child popup centered over its parent application surface."""
    _center_over_parent(parent, popup)
    if hasattr(popup, "show"):
        popup.show()
    if hasattr(popup, "raise_"):
        popup.raise_()
    if hasattr(popup, "activateWindow"):
        popup.activateWindow()


def show_tool_popup(parent: Any, popup: Any) -> None:
    """Show a movable tool window at its saved geometry or centered initially."""
    if not getattr(popup, "_dnd_geometry_restore_attempted", False):
        popup._dnd_geometry_restored = _restore_tool_geometry(
            getattr(popup, "_dnd_tool_qt", None),
            popup,
            getattr(popup, "_dnd_tool_key", "tool"),
        )
        popup._dnd_geometry_restore_attempted = True
    if not getattr(popup, "_dnd_geometry_restored", False):
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
    origin_x, origin_y = _parent_window_origin(parent, popup)
    popup.move(
        origin_x + max(0, (parent_width - popup_width) // 2),
        origin_y + max(0, (parent_height - popup_height) // 2),
    )


def _parent_window_origin(parent: Any, popup: Any) -> tuple[int, int]:
    is_window = getattr(popup, "isWindow", None)
    if not callable(is_window) or not is_window():
        return (0, 0)
    frame_geometry = getattr(parent, "frameGeometry", None)
    if not callable(frame_geometry):
        return (0, 0)
    geometry = frame_geometry()
    top_left = getattr(geometry, "topLeft", None)
    point = top_left() if callable(top_left) else None
    x = getattr(point, "x", None)
    y = getattr(point, "y", None)
    if not callable(x) or not callable(y):
        return (0, 0)
    return (int(x()), int(y()))


def _dimension(widget: Any, name: str) -> int:
    value = getattr(widget, name, None)
    return int(value()) if callable(value) else 0


def _is_escape_event(qt: Any, event: Any) -> bool:
    if not hasattr(event, "key"):
        return False
    qt_namespace = getattr(getattr(qt, "QtCore", None), "Qt", None)
    key_namespace = getattr(qt_namespace, "Key", qt_namespace)
    escape = getattr(key_namespace, "Key_Escape", None)
    if escape is None:
        escape = getattr(qt_namespace, "Key_Escape", None)
    return escape is not None and event.key() == escape


def _tool_window_flags(qt: Any) -> Any | None:
    qt_namespace = getattr(getattr(qt, "QtCore", None), "Qt", None)
    window_type = getattr(qt_namespace, "WindowType", qt_namespace)
    if window_type is None:
        return None
    flags = None
    for name in (
        "Tool",
        "WindowTitleHint",
        "WindowSystemMenuHint",
        "WindowCloseButtonHint",
    ):
        value = getattr(window_type, name, None)
        if value is not None:
            flags = value if flags is None else flags | value
    return flags


def _settings(qt: Any) -> Any | None:
    settings_class = getattr(getattr(qt, "QtCore", None), "QSettings", None)
    if settings_class is None:
        return None
    return settings_class(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)


def _restore_tool_geometry(qt: Any, popup: Any, key: str) -> bool:
    settings = _settings(qt)
    if settings is None or not hasattr(popup, "restoreGeometry"):
        return False
    geometry = settings.value(f"tool_windows/{key}/geometry")
    if geometry is None:
        return False
    return bool(popup.restoreGeometry(geometry))


def _save_tool_geometry(qt: Any, popup: Any, key: str) -> None:
    settings = _settings(qt)
    if settings is None or not hasattr(popup, "saveGeometry"):
        return
    settings.setValue(f"tool_windows/{key}/geometry", popup.saveGeometry())
    if hasattr(settings, "sync"):
        settings.sync()
