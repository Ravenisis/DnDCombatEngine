"""Main GUI window."""

from __future__ import annotations

from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp, create_app
from dnd_combat_engine.gui.qt import load_qt
from dnd_combat_engine.gui.theme import dark_theme_stylesheet
from dnd_combat_engine.gui.widgets import CharacterSheetWidget, CombatLogWidget, DiceTrayWidget


def create_main_window(app: DnDCombatEngineApp | None = None):
    """Create the main application window."""
    qt = load_qt()
    application = app or create_app(Path("data"))
    window = qt.QtWidgets.QMainWindow()
    window.setWindowTitle("DnDCombatEngine")
    window.resize(1200, 800)
    window.setStyleSheet(dark_theme_stylesheet())

    central = qt.QtWidgets.QLabel("Combat workspace")
    central.setAlignment(qt.QtCore.Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(central)

    _add_dock(window, qt, "Character Sheet", CharacterSheetWidget.create(application, qt))
    _add_dock(window, qt, "Combat Log", CombatLogWidget.create(qt))
    _add_dock(window, qt, "Dice Tray", DiceTrayWidget.create(application, qt))
    return window


def run_gui(data_root: Path | str = "data") -> int:
    """Run the PySide6 GUI application."""
    qt = load_qt()
    app = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    window = create_main_window(create_app(data_root))
    window.show()
    return int(app.exec())


def _add_dock(window, qt, title: str, widget) -> None:
    dock = qt.QtWidgets.QDockWidget(title, window)
    dock.setWidget(widget)
    window.addDockWidget(qt.QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dock)

