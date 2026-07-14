"""Headless PySide6 checks exercised by the full cross-platform test suite."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.gui
def test_main_window_embeds_and_closes_preferences_popup() -> None:
    """Create the real main window and verify an in-window popup interaction."""
    pytest.importorskip("PySide6")

    from dnd_combat_engine.app import create_app
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    data_root = Path(__file__).resolve().parents[1] / "data"
    window = main_window.create_main_window(create_app(data_root))
    try:
        main_window._open_preferences_window(window, qt)
        application.processEvents()

        popup = window._dnd_named_popups["preferences"]  # noqa: SLF001
        assert popup.parent() is window
        assert not popup.isWindow()
        assert popup.findChild(qt.QtWidgets.QComboBox) is not None
        close_button = next(
            button
            for button in popup.findChildren(qt.QtWidgets.QPushButton)
            if button.text() == "Close"
        )
        close_button.click()
        application.processEvents()
        assert "preferences" not in window._dnd_named_popups  # noqa: SLF001
    finally:
        window.close()
