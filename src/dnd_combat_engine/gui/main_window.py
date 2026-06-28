"""Main GUI window."""

from __future__ import annotations

from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp, create_app
from dnd_combat_engine.gui.actions import action_specs_by_menu, default_action_specs
from dnd_combat_engine.gui.qt import load_qt
from dnd_combat_engine.gui.session import GuiSession
from dnd_combat_engine.gui.theme import dark_theme_stylesheet
from dnd_combat_engine.gui.widgets import (
    AttackPanelWidget,
    CharacterSheetWidget,
    CombatLogWidget,
    DiceTrayWidget,
    EncounterTrackerWidget,
    InitiativeWidget,
)


def create_main_window(app: DnDCombatEngineApp | None = None):
    """Create the main application window."""
    qt = load_qt()
    application = app or create_app(Path("data"))
    session = GuiSession()
    window = qt.QtWidgets.QMainWindow()
    window.setWindowTitle("DnDCombatEngine")
    window.resize(session.window_width, session.window_height)
    window.setStyleSheet(dark_theme_stylesheet())

    central = qt.QtWidgets.QLabel("Combat workspace")
    central.setAlignment(qt.QtCore.Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(central)

    _add_dock(window, qt, "Character Sheet", CharacterSheetWidget.create(application, qt))
    _add_dock(window, qt, "Combat Log", CombatLogWidget.create(qt))
    _add_dock(window, qt, "Dice Tray", DiceTrayWidget.create(application, qt))
    _add_dock(window, qt, "Encounter", EncounterTrackerWidget.create(application, qt))
    _add_dock(window, qt, "Initiative", InitiativeWidget.create(application, qt))
    _add_dock(window, qt, "Attack", AttackPanelWidget.create(application, qt))
    _configure_menus(window, qt)
    _set_status(window, "Ready")
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


def _configure_menus(window, qt) -> None:
    menu_bar = window.menuBar()
    for menu_name, specs in action_specs_by_menu(default_action_specs()).items():
        menu = menu_bar.addMenu(menu_name)
        for spec in specs:
            action = qt.QtWidgets.QAction(spec.text, window)
            if spec.shortcut and hasattr(action, "setShortcut"):
                action.setShortcut(spec.shortcut)
            if hasattr(action, "setStatusTip"):
                action.setStatusTip(spec.status_tip)
            menu.addAction(action)


def _set_status(window, message: str) -> None:
    window.statusBar().showMessage(message)
