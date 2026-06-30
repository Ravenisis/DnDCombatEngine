"""Main GUI window."""

from __future__ import annotations

from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp, create_app
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.gui.actions import action_specs_by_menu, default_action_specs
from dnd_combat_engine.gui.editors import (
    import_character_pdf_to_campaign,
    import_character_url_to_campaign,
)
from dnd_combat_engine.gui.import_dialogs import ask_character_url, choose_character_pdf
from dnd_combat_engine.gui.qt import load_qt
from dnd_combat_engine.gui.session import GuiSession
from dnd_combat_engine.gui.theme import dark_theme_stylesheet
from dnd_combat_engine.gui.widgets import (
    AbilitiesWidget,
    ActionBarWidget,
    AttackPanelWidget,
    CampaignEditorWidget,
    CampaignWidget,
    CharacterSheetWidget,
    CombatLogWidget,
    DiceTrayWidget,
    EncounterEditorWidget,
    EncounterTrackerWidget,
    InitiativeWidget,
    SpellbookWidget,
)


def create_main_window(app: DnDCombatEngineApp | None = None):
    """Create the main application window."""
    qt = load_qt()
    application = app or create_app(Path("data"))
    session = GuiSession()
    window = qt.QtWidgets.QMainWindow()
    action_bar_session = ActionBarSession()
    window.setWindowTitle("DnDCombatEngine")
    window.resize(session.window_width, session.window_height)
    window.setStyleSheet(dark_theme_stylesheet())

    central = qt.QtWidgets.QLabel("Combat workspace")
    central.setAlignment(qt.QtCore.Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(central)

    _add_dock(window, qt, "Campaign", CampaignWidget.create(application, qt))
    _add_dock(window, qt, "Campaign Editor", CampaignEditorWidget.create(application, qt))
    _add_dock(window, qt, "Character Sheet", CharacterSheetWidget.create(application, qt))
    _add_dock(window, qt, "Combat Log", CombatLogWidget.create(qt))
    _add_dock(window, qt, "Dice Tray", DiceTrayWidget.create(application, qt))
    _add_dock(window, qt, "Encounter", EncounterTrackerWidget.create(application, qt))
    _add_dock(window, qt, "Encounter Editor", EncounterEditorWidget.create(application, qt))
    _add_dock(window, qt, "Initiative", InitiativeWidget.create(application, qt))
    _add_dock(window, qt, "Attack", AttackPanelWidget.create(application, qt))
    _add_dock(window, qt, "Spellbook", SpellbookWidget.create(application, qt, action_bar_session))
    _add_dock(window, qt, "Abilities", AbilitiesWidget.create(application, qt, action_bar_session))
    _add_bottom_dock(window, qt, "Action Bar", ActionBarWidget.create(qt, action_bar_session))
    _configure_menus(window, qt, application)
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


def _add_bottom_dock(window, qt, title: str, widget) -> None:
    dock = qt.QtWidgets.QDockWidget(title, window)
    dock.setWidget(widget)
    window.addDockWidget(qt.QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, dock)


def _configure_menus(window, qt, app: DnDCombatEngineApp) -> None:
    menu_bar = window.menuBar()
    action_class = getattr(getattr(qt, "QtGui", None), "QAction", None)
    if action_class is None:
        action_class = qt.QtWidgets.QAction
    for menu_name, specs in action_specs_by_menu(default_action_specs()).items():
        menu = menu_bar.addMenu(menu_name)
        submenus = {}
        for spec in specs:
            action = action_class(spec.text, window)
            if spec.shortcut and hasattr(action, "setShortcut"):
                action.setShortcut(spec.shortcut)
            if hasattr(action, "setStatusTip"):
                action.setStatusTip(spec.status_tip)
            if hasattr(action, "triggered"):
                action.triggered.connect(
                    lambda checked=False, action_id=spec.action_id: _run_menu_action(
                        window,
                        qt,
                        app,
                        action_id,
                    )
                )
            target_menu = menu
            if spec.submenu:
                target_menu = submenus.get(spec.submenu)
                if target_menu is None:
                    target_menu = menu.addMenu(spec.submenu)
                    submenus[spec.submenu] = target_menu
            target_menu.addAction(action)


def _run_menu_action(window, qt, app: DnDCombatEngineApp, action_id: str) -> None:
    if action_id == "file.exit":
        window.close()
        return
    if action_id == "campaign.import_pdf":
        _import_pdf_from_menu(window, qt, app)
        return
    if action_id == "campaign.import_url":
        _import_url_from_menu(window, qt, app)
        return
    _set_status(window, f"{action_id} selected.")


def _import_pdf_from_menu(window, qt, app: DnDCombatEngineApp) -> None:
    path = choose_character_pdf(qt, window)
    if not path:
        _set_status(window, "Character PDF import canceled.")
        return
    _run_import(
        window,
        qt,
        lambda: import_character_pdf_to_campaign(app, "starter_campaign", path),
    )


def _import_url_from_menu(window, qt, app: DnDCombatEngineApp) -> None:
    url = ask_character_url(qt, window)
    if not url:
        _set_status(window, "Character URL import canceled.")
        return
    _run_import(
        window,
        qt,
        lambda: import_character_url_to_campaign(app, "starter_campaign", url),
    )


def _run_import(window, qt, action) -> None:
    try:
        message = action()
    except ValueError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    except KeyError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    _show_message(window, qt, "Character Imported", message)


def _show_message(window, qt, title: str, message: str, error: bool = False) -> None:
    message_box = getattr(qt.QtWidgets, "QMessageBox", None)
    if message_box is not None:
        method_name = "warning" if error else "information"
        method = getattr(message_box, method_name, None)
        if method is not None:
            method(window, title, message)
    _set_status(window, message)


def _set_status(window, message: str) -> None:
    window.statusBar().showMessage(message)

