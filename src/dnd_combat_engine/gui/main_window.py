"""Main GUI window."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp, create_app
from dnd_combat_engine.controllers import CombatActionRequest
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.gui.actions import action_specs_by_menu, default_action_specs
from dnd_combat_engine.gui.import_dialogs import (
    ask_campaign_name,
    ask_character_id,
    ask_character_url,
    choose_character_pdf,
    review_character_import,
)
from dnd_combat_engine.gui.qt import load_qt
from dnd_combat_engine.gui.session import GuiSession
from dnd_combat_engine.gui.theme import (
    dark_theme_stylesheet,
    high_contrast_theme_stylesheet,
    parchment_theme_stylesheet,
)
from dnd_combat_engine.gui.widgets import (
    AbilitiesWidget,
    ActionBarWidget,
    AttackPanelWidget,
    CampaignActivityWidget,
    CampaignEditorWidget,
    CampaignWidget,
    CharacterSheetWidget,
    CombatLogWidget,
    EncounterTrackerWidget,
    InventoryWidget,
    PartyFramesWidget,
    SavingThrowWidget,
    SpellbookWidget,
    SpellSlotTrackerWidget,
    TargetPanelWidget,
)
from dnd_combat_engine.models import (
    ActionBarActionKind,
    ActionBarButton,
    BetaBugReport,
    Campaign,
    Character,
    ConcentrationState,
    ConditionName,
    EffectDefinition,
    EffectKind,
    EffectResolution,
    InventoryItem,
    ItemCategory,
    ParticipantKind,
    TargetKind,
    TargetProfile,
    TargetReference,
    ensure_spell_slot_resources,
)
from dnd_combat_engine.models.damage import DamageProfile
from dnd_combat_engine.rules import EffectPlan, EffectResolver


@dataclass(slots=True)
class GuiCampaignState:
    """Mutable GUI state for the currently open campaign workspace."""

    active_campaign_id: str | None = "starter_campaign"
    selected_character_id: str | None = "ravenisis"
    party_leader_character_id: str | None = "ravenisis"
    party_initiative: dict[str, int] = field(default_factory=dict)
    concentration_character_id: str | None = None
    concentration_spell_id: str | None = None
    active_concentration: ConcentrationState | None = None
    beacon_of_hope_targets: tuple[str, ...] = field(default_factory=tuple)
    bless_targets: tuple[str, ...] = field(default_factory=tuple)
    active_target: TargetReference | None = None
    last_dice_notation: str = "1d20"


def create_main_window(app: DnDCombatEngineApp | None = None):
    """Create the main application window."""
    qt = load_qt()
    application = app or create_app(Path("data"))
    session = GuiSession()
    window = qt.QtWidgets.QMainWindow()
    action_bar_session = ActionBarSession()
    campaign_state = GuiCampaignState()
    _load_campaign_concentration(application, campaign_state)
    window._dnd_campaign_state = campaign_state  # noqa: SLF001
    window.setWindowTitle("DnDCombatEngine")
    _set_window_icon(window, qt)
    window.resize(session.window_width, session.window_height)
    window.setStyleSheet(dark_theme_stylesheet())
    if hasattr(window, "setDockNestingEnabled"):
        window.setDockNestingEnabled(True)

    workspace = qt.QtWidgets.QTextEdit()
    workspace.setReadOnly(True)
    workspace.append("Combat Workspace")
    window._dnd_central = workspace  # noqa: SLF001
    window._dnd_docks = {}  # noqa: SLF001
    window._dnd_panel_hosts = {}  # noqa: SLF001
    window.setCentralWidget(_main_workspace(window, qt, workspace))

    _add_left_panel(window, qt, "Campaign", _campaign_widget(application, qt, campaign_state))
    _add_left_panel(
        window,
        qt,
        "Activity",
        _activity_widget(application, qt, campaign_state),
    )
    _add_left_panel(window, qt, "Party", _party_widget(window, application, qt, campaign_state))
    _add_left_panel(
        window,
        qt,
        "Target",
        _target_widget(window, application, qt, campaign_state),
    )
    _add_left_panel(
        window,
        qt,
        "Campaign Editor",
        _campaign_editor_widget(application, qt, campaign_state),
    )
    _add_left_panel(window, qt, "Combat Log", CombatLogWidget.create(qt))
    _add_left_panel(window, qt, "Encounter", EncounterTrackerWidget.create(application, qt))
    _add_left_panel(
        window,
        qt,
        "Attack",
        AttackPanelWidget.create(
            application,
            qt,
            character_id=_active_character_id(campaign_state),
            campaign_id=campaign_state.active_campaign_id or "starter_campaign",
        ),
    )
    window._dnd_action_bar_session = action_bar_session  # noqa: SLF001
    window._dnd_action_bar_on_activate = lambda slot, shift_pressed: _activate_action_bar_slot(  # noqa: SLF001
        window,
        qt,
        application,
        campaign_state,
        action_bar_session,
        slot,
        shift_pressed,
    )
    window._dnd_popups = []  # noqa: SLF001
    window._dnd_named_popups = {}  # noqa: SLF001
    _add_bottom_dock(
        window,
        qt,
        "Action Bar",
        _action_bar_widget(
            application,
            qt,
            campaign_state,
            action_bar_session,
            window._dnd_action_bar_on_activate,  # noqa: SLF001
            on_save=lambda ability: _roll_saving_throw(
                window,
                application,
                campaign_state,
                ability,
            ),
        ),
    )
    _configure_menus(window, qt, application, campaign_state)
    _set_status(window, "Ready")
    return window


def run_gui(data_root: Path | str = "data") -> int:
    """Run the PySide6 GUI application."""
    qt = load_qt()
    app = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    window = create_main_window(create_app(data_root))
    window.show()
    return int(app.exec())


def _set_window_icon(window, qt) -> None:
    """Set the packaged Windows icon when Qt supports it."""
    icon_path = Path(__file__).resolve().parents[1] / "data" / "app_icon.ico"
    icon_class = getattr(qt.QtGui, "QIcon", None)
    if not icon_path.exists() or icon_class is None or not hasattr(window, "setWindowIcon"):
        return
    window.setWindowIcon(icon_class(str(icon_path)))


def _main_workspace(window, qt, workspace):
    left_content = qt.QtWidgets.QWidget()
    left_layout = qt.QtWidgets.QVBoxLayout(left_content)
    if hasattr(left_layout, "setContentsMargins"):
        left_layout.setContentsMargins(6, 6, 6, 6)
    if hasattr(left_layout, "setSpacing"):
        left_layout.setSpacing(6)
    window._dnd_left_layout = left_layout  # noqa: SLF001

    left_scroll = _scroll_area(qt, left_content)
    _set_size_constraint(left_scroll, "setMinimumWidth", 520)
    _set_size_constraint(left_scroll, "setMaximumWidth", 980)
    _set_size_constraint(workspace, "setMinimumWidth", 360)
    splitter_class = getattr(qt.QtWidgets, "QSplitter", None)
    if splitter_class is not None:
        orientation = getattr(getattr(qt.QtCore.Qt, "Orientation", None), "Horizontal", None)
        if orientation is None:
            orientation = getattr(qt.QtCore.Qt, "Horizontal", None)
        splitter = splitter_class(orientation)
        splitter.addWidget(left_scroll)
        splitter.addWidget(workspace)
        if hasattr(splitter, "setCollapsible"):
            splitter.setCollapsible(0, False)
            splitter.setCollapsible(1, False)
        if hasattr(splitter, "setStretchFactor"):
            splitter.setStretchFactor(0, 2)
            splitter.setStretchFactor(1, 1)
        if hasattr(splitter, "setSizes"):
            splitter.setSizes([800, 400])
        return splitter

    container = qt.QtWidgets.QWidget()
    layout = qt.QtWidgets.QHBoxLayout(container)
    _layout_add_widget(layout, left_scroll, 2)
    _layout_add_widget(layout, workspace, 1)
    return container


def _set_size_constraint(widget, method_name: str, value: int) -> None:
    method = getattr(widget, method_name, None)
    if method is not None:
        method(value)


def _scroll_area(qt, widget):
    scroll_class = getattr(qt.QtWidgets, "QScrollArea", None)
    if scroll_class is None:
        return widget
    scroll = scroll_class()
    if hasattr(scroll, "setWidgetResizable"):
        scroll.setWidgetResizable(True)
    if hasattr(scroll, "setWidget"):
        scroll.setWidget(widget)
    return scroll


def _add_left_panel(window, qt, title: str, widget) -> None:
    layout = getattr(window, "_dnd_left_layout", None)
    if layout is None:
        return
    host = _panel_host(qt, title, widget)
    _layout_add_widget(layout, host)
    if hasattr(window, "_dnd_panel_hosts"):
        window._dnd_panel_hosts[title] = host  # noqa: SLF001


def _panel_host(qt, title: str, widget):
    host_class = getattr(qt.QtWidgets, "QGroupBox", qt.QtWidgets.QWidget)
    try:
        host = host_class(title)
    except TypeError:
        host = host_class()
    layout = qt.QtWidgets.QVBoxLayout(host)
    _layout_add_widget(layout, widget)
    host._dnd_panel_layout = layout  # noqa: SLF001
    host._dnd_panel_widget = widget  # noqa: SLF001
    return host


def _layout_add_widget(layout, widget, stretch: int | None = None) -> None:
    if stretch is None:
        layout.addWidget(widget)
        return
    try:
        layout.addWidget(widget, stretch)
    except TypeError:
        layout.addWidget(widget)


def _add_dock(window, qt, title: str, widget) -> None:
    dock = qt.QtWidgets.QDockWidget(title, window)
    dock.setWidget(widget)
    _configure_dock(qt, dock, qt.QtCore.Qt.DockWidgetArea.LeftDockWidgetArea)
    window.addDockWidget(qt.QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dock)
    if hasattr(window, "_dnd_docks"):
        window._dnd_docks[title] = dock  # noqa: SLF001


def _add_bottom_dock(window, qt, title: str, widget) -> None:
    dock = qt.QtWidgets.QDockWidget(title, window)
    dock.setWidget(widget)
    _configure_dock(qt, dock, qt.QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
    window.addDockWidget(qt.QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, dock)
    if hasattr(window, "_dnd_docks"):
        window._dnd_docks[title] = dock  # noqa: SLF001


def _configure_dock(qt, dock, allowed_area) -> None:
    if hasattr(dock, "setAllowedAreas"):
        dock.setAllowedAreas(allowed_area)
    if hasattr(dock, "setFloating"):
        dock.setFloating(False)
    features = _dock_features(qt)
    if features is not None and hasattr(dock, "setFeatures"):
        dock.setFeatures(features)


def _dock_features(qt):
    dock_class = qt.QtWidgets.QDockWidget
    feature_class = getattr(dock_class, "DockWidgetFeature", dock_class)
    features = [
        getattr(feature_class, "DockWidgetClosable", None),
        getattr(feature_class, "DockWidgetMovable", None),
    ]
    enabled_features = [feature for feature in features if feature is not None]
    if not enabled_features:
        return None
    combined = enabled_features[0]
    for feature in enabled_features[1:]:
        combined |= feature
    return combined


def _configure_menus(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
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
                        state,
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


def _run_menu_action(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    action_id: str,
) -> None:
    if action_id == "file.exit":
        window.close()
        return
    if action_id == "character.spellbook":
        _open_spellbook_window(window, qt, app, state)
        return
    if action_id == "character.abilities":
        _open_abilities_window(window, qt, app, state)
        return
    if action_id == "character.inventory":
        _open_inventory_window(window, qt, app, state)
        return
    if action_id == "character.break_concentration":
        _break_concentration_from_menu(window, qt, app, state)
        return
    if action_id.startswith("dice.roll_d"):
        notation = _dice_notation_from_action(action_id)
        if notation is None:
            _set_status(window, f"{action_id} selected.")
            return
        _roll_menu_die(window, app, state, notation)
        return
    if action_id == "dice.repeat_last":
        _roll_menu_die(window, app, state, state.last_dice_notation)
        return
    if action_id == "campaign.load_starter":
        _open_campaign(window, qt, app, state, "starter_campaign")
        return
    if action_id == "campaign.activate_starter":
        campaign = app.campaigns.activate(app.campaigns.load("starter_campaign"))
        app.campaigns.save(campaign)
        _open_campaign(window, qt, app, state, campaign.campaign_id)
        return
    if action_id == "campaign.new":
        _begin_new_campaign(window, qt, app, state)
        return
    if action_id == "campaign.close":
        _close_campaign(window, qt, app, state)
        return
    if action_id == "campaign.add_party_member":
        _add_party_member_from_menu(window, qt, app, state)
        return
    if action_id == "campaign.set_party_leader":
        _set_party_leader_from_menu(window, qt, app, state)
        return
    if action_id == "campaign.long_rest":
        _rest_campaign(window, qt, app, state, long_rest=True)
        return
    if action_id == "campaign.short_rest":
        _rest_campaign(window, qt, app, state, long_rest=False)
        return
    if action_id == "campaign.import_pdf":
        _import_pdf_from_menu(window, qt, app, state)
        return
    if action_id == "campaign.import_url":
        _import_url_from_menu(window, qt, app, state)
        return
    if action_id == "settings.key_binds":
        _open_key_binds_window(window, qt)
        return
    if action_id == "settings.preferences":
        _open_preferences_window(window, qt)
        return
    if action_id == "help.report_bug":
        _report_bug_from_menu(window, qt, app)
        return
    if action_id == "help.about":
        _show_message(
            window,
            qt,
            "About DnDCombatEngine",
            "DnDCombatEngine 1.0.1\nLayered Dungeons & Dragons combat workspace.",
        )
        return
    _set_status(window, f"{action_id} selected.")


def _report_bug_from_menu(window, qt, app: DnDCombatEngineApp) -> None:
    report = _ask_bug_report(qt, window)
    if report is None:
        _set_status(window, "Bug report canceled.")
        return
    try:
        path = app.beta_reports.submit_bug_report(report)
    except (OSError, ValueError) as exc:
        _show_message(window, qt, "Report Bug Failed", str(exc), error=True)
        _set_status(window, str(exc))
        return
    _show_message(
        window,
        qt,
        "Bug Report Saved",
        f"Saved beta tester report to:\n{path}",
    )
    _set_status(window, f"Saved bug report to {path}.")


def _ask_bug_report(qt, parent) -> BetaBugReport | None:
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    if dialog_class is None:
        return None

    dialog = dialog_class(parent)
    if hasattr(dialog, "setWindowTitle"):
        dialog.setWindowTitle("Report Bug")
    if hasattr(dialog, "resize"):
        dialog.resize(560, 620)

    layout = qt.QtWidgets.QVBoxLayout(dialog)
    summary = qt.QtWidgets.QLineEdit()
    tester = qt.QtWidgets.QLineEdit()
    severity = _combo_box(qt, ("Medium", "Low", "High", "Critical"))
    area = _combo_box(
        qt,
        (
            "General",
            "Character Import",
            "Campaign",
            "Combat",
            "Action Bar",
            "Inventory",
            "Installer",
            "Documentation",
        ),
    )
    description = qt.QtWidgets.QTextEdit()
    steps = qt.QtWidgets.QTextEdit()
    expected = qt.QtWidgets.QTextEdit()
    actual = qt.QtWidgets.QTextEdit()

    _add_form_row(qt, layout, "Summary", summary)
    _add_form_row(qt, layout, "Tester", tester)
    _add_form_row(qt, layout, "Severity", severity)
    _add_form_row(qt, layout, "Area", area)
    _add_labeled_text(qt, layout, "Description", description)
    _add_labeled_text(qt, layout, "Steps To Reproduce", steps)
    _add_labeled_text(qt, layout, "Expected Result", expected)
    _add_labeled_text(qt, layout, "Actual Result", actual)

    buttons = _bug_report_dialog_buttons(qt, dialog)
    if buttons is not None:
        _connect_bug_report_dialog_buttons(qt, dialog, buttons, summary, description)
        layout.addWidget(buttons)

    if not _bug_report_dialog_accepted(qt, dialog):
        return None
    return BetaBugReport(
        summary=_line_edit_text(summary),
        description=_text_edit_text(description),
        steps_to_reproduce=_text_edit_text(steps),
        expected_result=_text_edit_text(expected),
        actual_result=_text_edit_text(actual),
        severity=_combo_text(severity),
        area=_combo_text(area),
        tester_name=_line_edit_text(tester),
    )


def _combo_box(qt, values: tuple[str, ...]):
    combo_class = getattr(qt.QtWidgets, "QComboBox", None)
    if combo_class is None:
        label = qt.QtWidgets.QLineEdit(values[0] if values else "")
        return label
    combo = combo_class()
    for value in values:
        combo.addItem(value)
    return combo


def _add_form_row(qt, layout, label: str, widget) -> None:
    row = qt.QtWidgets.QWidget()
    row_layout = qt.QtWidgets.QHBoxLayout(row)
    row_layout.addWidget(qt.QtWidgets.QLabel(label))
    row_layout.addWidget(widget)
    layout.addWidget(row)


def _add_labeled_text(qt, layout, label: str, widget) -> None:
    layout.addWidget(qt.QtWidgets.QLabel(label))
    layout.addWidget(widget)


def _bug_report_dialog_buttons(qt, dialog):
    button_box = getattr(qt.QtWidgets, "QDialogButtonBox", None)
    if button_box is None:
        return None
    button_mask = _dialog_buttons(button_box)
    buttons = button_box(button_mask) if button_mask is not None else button_box()
    if hasattr(buttons, "rejected"):
        buttons.rejected.connect(dialog.reject)
    return buttons


def _connect_bug_report_dialog_buttons(qt, dialog, buttons, summary, description) -> None:
    if not hasattr(buttons, "accepted"):
        return

    def accept_if_valid() -> None:
        if not _line_edit_text(summary):
            _show_dialog_warning(qt, dialog, "Report Bug", "Summary is required.")
            return
        if not _text_edit_text(description):
            _show_dialog_warning(qt, dialog, "Report Bug", "Description is required.")
            return
        dialog.accept()

    buttons.accepted.connect(accept_if_valid)


def _show_dialog_warning(qt, parent, title: str, message: str) -> None:
    message_box = getattr(qt.QtWidgets, "QMessageBox", None)
    if message_box is None:
        return
    warning = getattr(message_box, "warning", None)
    if warning is not None:
        warning(parent, title, message)


def _bug_report_dialog_accepted(qt, dialog) -> bool:
    result = dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()
    dialog_code = getattr(getattr(qt.QtWidgets.QDialog, "DialogCode", None), "Accepted", None)
    if dialog_code is None:
        dialog_code = getattr(qt.QtWidgets.QDialog, "Accepted", 1)
    return result == dialog_code or result is True


def _line_edit_text(widget) -> str:
    return str(widget.text()).strip() if hasattr(widget, "text") else ""


def _text_edit_text(widget) -> str:
    if hasattr(widget, "toPlainText"):
        return str(widget.toPlainText()).strip()
    if hasattr(widget, "text"):
        return str(widget.text()).strip()
    return ""


def _combo_text(widget) -> str:
    if hasattr(widget, "currentText"):
        return str(widget.currentText()).strip()
    return _line_edit_text(widget)


def _import_pdf_from_menu(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Import Failed", "Open or create a campaign first.", error=True)
        return
    path = choose_character_pdf(qt, window)
    if not path:
        _set_status(window, "Character PDF import canceled.")
        return
    try:
        draft = app.character_imports.preview_pdf(path)
    except ValueError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    reviewed = review_character_import(qt, window, draft)
    if reviewed is None:
        _set_status(window, "Character PDF import canceled.")
        return
    _run_import_result(
        window,
        qt,
        app,
        state,
        lambda: app.character_imports.import_draft_to_campaign(
            reviewed,
            state.active_campaign_id or "",
        ),
    )


def _import_url_from_menu(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Import Failed", "Open or create a campaign first.", error=True)
        return
    url = ask_character_url(qt, window)
    if not url:
        _set_status(window, "Character URL import canceled.")
        return
    if not hasattr(app.character_imports, "preview_url"):
        _run_import_result(
            window,
            qt,
            app,
            state,
            lambda: app.character_imports.import_url_to_campaign(
                url,
                state.active_campaign_id or "",
            ),
        )
        return
    try:
        draft = app.character_imports.preview_url(url)
    except ValueError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    reviewed = review_character_import(qt, window, draft)
    if reviewed is None:
        _set_status(window, "Character URL import canceled.")
        return
    _run_import_result(
        window,
        qt,
        app,
        state,
        lambda: app.character_imports.import_draft_to_campaign(
            reviewed,
            state.active_campaign_id or "",
        ),
    )


def _run_import_result(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    action,
) -> None:
    try:
        result = action()
    except ValueError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    except KeyError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    state.active_campaign_id = result.campaign.campaign_id
    state.selected_character_id = result.character.character_id
    if state.party_leader_character_id is None:
        state.party_leader_character_id = result.character.character_id
    state.party_initiative.pop(result.character.character_id, None)
    _record_campaign_activity(
        app,
        state,
        f"Imported {result.character.name} into {result.campaign.name}.",
        "import",
    )
    _refresh_campaign_docks(window, qt, app, state)
    message = (
        f"Imported {result.character.name} as {result.character.character_id} "
        f"and added them to {result.campaign.name}."
    )
    _show_message(window, qt, "Character Imported", message)


def _open_campaign(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    campaign_id: str,
) -> None:
    campaign = app.campaigns.load(campaign_id)
    state.active_campaign_id = campaign.campaign_id
    state.selected_character_id = campaign.character_ids[0] if campaign.character_ids else None
    state.party_leader_character_id = state.selected_character_id
    state.active_target = None
    _apply_concentration_to_state(state, campaign.active_concentration)
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Opened {campaign.name}.")


def _close_campaign(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
    state.active_campaign_id = None
    state.selected_character_id = None
    state.party_leader_character_id = None
    state.active_target = None
    state.party_initiative.clear()
    _clear_concentration(state)
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, "Campaign closed.")


def _begin_new_campaign(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
    name = ask_campaign_name(qt, window)
    if not name:
        _set_status(window, "New campaign canceled.")
        return
    campaign_id = _unique_campaign_id(app, name)
    campaign = Campaign(campaign_id=campaign_id, name=name)
    app.campaigns.save(campaign)
    state.active_campaign_id = campaign.campaign_id
    state.selected_character_id = None
    state.party_leader_character_id = None
    state.active_target = None
    state.party_initiative.clear()
    _clear_concentration(state)
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Created {campaign.name}.")


def _refresh_campaign_docks(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    docks = getattr(window, "_dnd_docks", {})
    panels = getattr(window, "_dnd_panel_hosts", {})
    _replace_panel_widget(panels, "Campaign", _campaign_widget(app, qt, state))
    _replace_panel_widget(panels, "Activity", _activity_widget(app, qt, state))
    _replace_panel_widget(panels, "Party", _party_widget(window, app, qt, state))
    _replace_panel_widget(panels, "Target", _target_widget(window, app, qt, state))
    _replace_panel_widget(panels, "Campaign Editor", _campaign_editor_widget(app, qt, state))
    _replace_panel_widget(panels, "Character Sheet", _character_widget(app, qt, state))
    _replace_dock_widget(docks, "Campaign", _campaign_widget(app, qt, state))
    _replace_dock_widget(docks, "Activity", _activity_widget(app, qt, state))
    _replace_dock_widget(docks, "Party", _party_widget(window, app, qt, state))
    _replace_dock_widget(docks, "Target", _target_widget(window, app, qt, state))
    _replace_dock_widget(docks, "Campaign Editor", _campaign_editor_widget(app, qt, state))
    _replace_dock_widget(docks, "Character Sheet", _character_widget(app, qt, state))
    session = getattr(window, "_dnd_action_bar_session", None)
    if session is not None:
        _replace_panel_widget(panels, "Abilities", _abilities_widget(app, qt, state, session))
        _replace_dock_widget(docks, "Abilities", _abilities_widget(app, qt, state, session))
        on_activate = getattr(window, "_dnd_action_bar_on_activate", None)
        if on_activate is not None:
            _replace_dock_widget(
                docks,
                "Action Bar",
                _action_bar_widget(
                    app,
                    qt,
                    state,
                    session,
                    on_activate,
                    on_save=lambda ability: _roll_saving_throw(
                        window,
                        app,
                        state,
                        ability,
                    ),
                ),
            )


def _add_party_member_from_menu(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Add Failed", "Open or create a campaign first.", error=True)
        return
    existing_ids = tuple(app.characters.list_ids())
    character_id = ask_character_id(
        qt,
        window,
        "Add Party Member",
        "Character id:",
        existing_ids,
    )
    if not character_id:
        _set_status(window, "Add party member canceled.")
        return
    try:
        character = app.characters.load(character_id)
        campaign = app.campaigns.add_character(
            app.campaigns.load(state.active_campaign_id),
            character_id,
        )
        app.campaigns.save(campaign)
    except (KeyError, ValueError) as exc:
        _show_message(window, qt, "Add Failed", str(exc), error=True)
        return
    state.selected_character_id = character.character_id
    if state.party_leader_character_id is None:
        state.party_leader_character_id = character.character_id
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Added {character.name} to party.")


def _set_party_leader_from_menu(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Leader Failed", "Open or create a campaign first.", error=True)
        return
    campaign = app.campaigns.load(state.active_campaign_id)
    if not campaign.character_ids:
        _show_message(
            window,
            qt,
            "Leader Failed",
            "The active campaign has no party members.",
            error=True,
        )
        return
    character_id = ask_character_id(
        qt,
        window,
        "Set Party Leader",
        "Party leader:",
        campaign.character_ids,
    )
    if not character_id:
        _set_status(window, "Set party leader canceled.")
        return
    if character_id not in campaign.character_ids:
        _show_message(
            window,
            qt,
            "Leader Failed",
            f"{character_id} is not in the active party.",
            error=True,
        )
        return
    state.party_leader_character_id = character_id
    state.selected_character_id = character_id
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Set {character_id} as party leader.")


def _rest_campaign(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    *,
    long_rest: bool,
) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Rest Failed", "Open or create a campaign first.", error=True)
        return
    try:
        campaign = app.campaigns.load(state.active_campaign_id)
    except KeyError as exc:
        _show_message(window, qt, "Rest Failed", str(exc), error=True)
        return
    rested_count = 0
    for character_id in campaign.character_ids:
        try:
            character = app.characters.load(character_id)
        except KeyError:
            continue
        ensure_spell_slot_resources(character)
        _rest_character(character, long_rest=long_rest)
        app.characters.save(character)
        rested_count += 1
    rest_name = "Long rest" if long_rest else "Short rest"
    member_text = "party member" if rested_count == 1 else "party members"
    detail = (
        "Hit points and spell slots restored."
        if long_rest
        else "Partial hit points and short-rest resources restored."
    )
    message = f"{rest_name} completed for {rested_count} {member_text}. {detail}"
    _record_campaign_activity(app, state, message, "rest")
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, message)


def _rest_character(character: Character, *, long_rest: bool) -> None:
    ensure_spell_slot_resources(character)
    if long_rest:
        character.hit_points.heal(character.hit_points.maximum)
        character.hit_points.temporary = 0
    else:
        character.hit_points.heal(max(1, character.hit_points.maximum // 2))
    for resource_name, resource in character.resources.items():
        if long_rest or not _is_spell_slot_resource(resource_name):
            resource.reset()


def _is_spell_slot_resource(resource_name: str) -> bool:
    return re.fullmatch(r"spell_slot_\d+", resource_name) is not None


def _open_spellbook_window(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    if _toggle_named_popup(window, "spellbook", "Closed spellbook."):
        return
    session = getattr(window, "_dnd_action_bar_session", None)
    if session is None:
        _show_message(window, qt, "Spellbook Failed", "Action bar is not ready.", error=True)
        return
    character_id = _active_character_id(state)
    if character_id is None:
        _show_message(
            window,
            qt,
            "Spellbook Failed",
            "Set a party leader before opening the spellbook.",
            error=True,
        )
        return
    try:
        character = app.characters.load(character_id)
    except KeyError:
        _show_message(
            window,
            qt,
            "Spellbook Failed",
            f"Party leader {character_id} could not be loaded.",
            error=True,
        )
        return

    popup = qt.QtWidgets.QDialog(window)
    if hasattr(popup, "setWindowTitle"):
        popup.setWindowTitle(f"{character.name} Spellbook")
    if hasattr(popup, "resize"):
        popup.resize(360, 520)
    layout = qt.QtWidgets.QVBoxLayout(popup)
    layout.addWidget(_spellbook_widget(app, qt, state, session))
    _show_popup(window, popup, key="spellbook")
    _set_status(window, f"Opened {character.name} spellbook.")


def _open_abilities_window(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    if _toggle_named_popup(window, "abilities", "Closed abilities."):
        return
    session = getattr(window, "_dnd_action_bar_session", None)
    if session is None:
        _show_message(window, qt, "Abilities Failed", "Action bar is not ready.", error=True)
        return
    character_id = _active_character_id(state)
    if character_id is None:
        _show_message(
            window,
            qt,
            "Abilities Failed",
            "Set a party leader before opening abilities.",
            error=True,
        )
        return
    try:
        character = app.characters.load(character_id)
    except KeyError:
        _show_message(
            window,
            qt,
            "Abilities Failed",
            f"Party leader {character_id} could not be loaded.",
            error=True,
        )
        return

    popup = qt.QtWidgets.QDialog(window)
    if hasattr(popup, "setWindowTitle"):
        popup.setWindowTitle(f"{character.name} Abilities")
    if hasattr(popup, "resize"):
        popup.resize(360, 520)
    layout = qt.QtWidgets.QVBoxLayout(popup)
    layout.addWidget(_abilities_widget(app, qt, state, session))
    _show_popup(window, popup, key="abilities")
    _set_status(window, f"Opened {character.name} abilities.")


def _open_inventory_window(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    if _toggle_named_popup(window, "inventory", "Closed inventory."):
        return
    character_id = _active_character_id(state)
    if character_id is None:
        _show_message(
            window,
            qt,
            "Inventory Failed",
            "Set a party leader before opening inventory.",
            error=True,
        )
        return
    try:
        character = app.characters.load(character_id)
    except KeyError:
        _show_message(
            window,
            qt,
            "Inventory Failed",
            f"Party leader {character_id} could not be loaded.",
            error=True,
        )
        return

    popup = qt.QtWidgets.QDialog(window)
    if hasattr(popup, "setWindowTitle"):
        popup.setWindowTitle(f"{character.name} Inventory")
    if hasattr(popup, "resize"):
        popup.resize(620, 520)
    layout = qt.QtWidgets.QVBoxLayout(popup)
    content = {"widget": None}

    def refresh_inventory() -> None:
        next_widget = InventoryWidget.create(
            app,
            qt,
            character_id,
            on_consume=lambda item_id: _consume_inventory_item(
                window,
                qt,
                app,
                state,
                character_id,
                item_id,
            ),
            on_currency_change=lambda delta_cp: _change_character_currency(
                window,
                app,
                character_id,
                delta_cp,
            ),
            on_add_item=lambda: _add_inventory_item_from_dialog(
                window,
                qt,
                app,
                state,
                character_id,
                refresh_inventory,
            ),
        )
        previous = content.get("widget")
        if previous is not None and hasattr(layout, "removeWidget"):
            layout.removeWidget(previous)
        layout.addWidget(next_widget)
        if previous is not None and hasattr(previous, "setParent"):
            previous.setParent(None)
        content["widget"] = next_widget

    refresh_inventory()
    _show_popup(window, popup, key="inventory")
    _set_status(window, f"Opened {character.name} inventory.")


def _add_inventory_item_from_dialog(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    character_id: str,
    refresh_inventory,
) -> None:
    item = _ask_inventory_item(qt, window)
    if item is None:
        _set_status(window, "Add item canceled.")
        return
    try:
        character = app.characters.load(character_id)
        app.inventory.add_item(character, item, autosave=True)
    except (KeyError, ValueError) as exc:
        _show_message(window, qt, "Add Item Failed", str(exc), error=True)
        return
    message = f"Added {item.quantity} x {item.name} to {character.name}."
    _record_campaign_activity(app, state, message, "inventory")
    refresh_inventory()
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, message)


def _ask_inventory_item(qt, parent) -> InventoryItem | None:
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    if dialog_class is None:
        return None
    dialog = dialog_class(parent)
    if hasattr(dialog, "setWindowTitle"):
        dialog.setWindowTitle("Add Inventory Item")
    layout = qt.QtWidgets.QVBoxLayout(dialog)
    name = qt.QtWidgets.QLineEdit()
    quantity = qt.QtWidgets.QLineEdit("1")
    weight = qt.QtWidgets.QLineEdit("0")
    price = qt.QtWidgets.QLineEdit("0")
    category = _combo_box(qt, tuple(item.value for item in ItemCategory))
    notes = qt.QtWidgets.QTextEdit()
    _add_form_row(qt, layout, "Name", name)
    _add_form_row(qt, layout, "Quantity", quantity)
    _add_form_row(qt, layout, "Category", category)
    _add_form_row(qt, layout, "Weight", weight)
    _add_form_row(qt, layout, "Price CP", price)
    _add_labeled_text(qt, layout, "Notes", notes)
    buttons = _standard_dialog_buttons(qt, dialog)
    if buttons is not None:
        layout.addWidget(buttons)
    if not _generic_dialog_accepted(qt, dialog):
        return None
    item_name = _line_edit_text(name).strip()
    if not item_name:
        raise ValueError("item name is required")
    item_id = _slug(item_name)
    return InventoryItem(
        item_id=item_id,
        name=item_name,
        quantity=int(_line_edit_text(quantity) or "1"),
        weight=float(_line_edit_text(weight) or "0"),
        category=ItemCategory(_combo_text(category)),
        notes=_text_edit_text(notes) or None,
        purchase_price_cp=int(_line_edit_text(price) or "0"),
    )


def _standard_dialog_buttons(qt, dialog):
    button_box = getattr(qt.QtWidgets, "QDialogButtonBox", None)
    if button_box is None:
        return None
    button_mask = _dialog_buttons(button_box)
    buttons = button_box(button_mask) if button_mask is not None else button_box()
    if hasattr(buttons, "accepted"):
        buttons.accepted.connect(dialog.accept)
    if hasattr(buttons, "rejected"):
        buttons.rejected.connect(dialog.reject)
    return buttons


def _generic_dialog_accepted(qt, dialog) -> bool:
    result = dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()
    return _dialog_accepted(qt.QtWidgets.QDialog, result)


def _open_key_binds_window(window, qt) -> None:
    if _toggle_named_popup(window, "key_binds", "Closed key binds."):
        return
    popup = qt.QtWidgets.QDialog(window)
    if hasattr(popup, "setWindowTitle"):
        popup.setWindowTitle("Key Binds")
    if hasattr(popup, "resize"):
        popup.resize(420, 420)
    layout = qt.QtWidgets.QVBoxLayout(popup)
    table_class = getattr(qt.QtWidgets, "QTableWidget", None)
    item_class = getattr(qt.QtWidgets, "QTableWidgetItem", None)
    rows = _key_bind_rows()
    if table_class is not None and item_class is not None:
        table = table_class(len(rows), 2)
        table.setHorizontalHeaderLabels(["Command", "Shortcut"])
        for row, (command, shortcut) in enumerate(rows):
            table.setItem(row, 0, item_class(command))
            table.setItem(row, 1, item_class(shortcut))
        if hasattr(table, "resizeColumnsToContents"):
            table.resizeColumnsToContents()
        layout.addWidget(table)
    else:
        label = qt.QtWidgets.QLabel(
            "\n".join(f"{command}: {shortcut}" for command, shortcut in rows)
        )
        layout.addWidget(label)
    _show_popup(window, popup, key="key_binds")
    _set_status(window, "Opened key binds.")


def _open_preferences_window(window, qt) -> None:
    if _toggle_named_popup(window, "preferences", "Closed preferences."):
        return
    popup = qt.QtWidgets.QDialog(window)
    if hasattr(popup, "setWindowTitle"):
        popup.setWindowTitle("Preferences")
    if hasattr(popup, "resize"):
        popup.resize(360, 180)
    layout = qt.QtWidgets.QVBoxLayout(popup)
    combo_class = getattr(qt.QtWidgets, "QComboBox", None)
    label = qt.QtWidgets.QLabel("Color Scheme")
    layout.addWidget(label)
    if combo_class is None:
        layout.addWidget(qt.QtWidgets.QLabel("Color scheme selection is unavailable."))
    else:
        combo = combo_class()
        schemes = ("Dark", "Parchment", "High Contrast")
        for scheme in schemes:
            combo.addItem(scheme)

        def apply_scheme(index: int) -> None:
            scheme = schemes[index] if 0 <= index < len(schemes) else "Dark"
            _apply_color_scheme(window, scheme)

        if hasattr(combo, "currentIndexChanged"):
            combo.currentIndexChanged.connect(apply_scheme)
        layout.addWidget(combo)
    _show_popup(window, popup, key="preferences")
    _set_status(window, "Opened preferences.")


def _show_popup(window, popup, key: str | None = None) -> None:
    popups = getattr(window, "_dnd_popups", [])
    popups.append(popup)
    window._dnd_popups = popups  # noqa: SLF001
    if key is not None:
        named = getattr(window, "_dnd_named_popups", {})
        named[key] = popup
        window._dnd_named_popups = named  # noqa: SLF001
    if hasattr(popup, "show"):
        popup.show()


def _toggle_named_popup(window, key: str, status_message: str) -> bool:
    named = getattr(window, "_dnd_named_popups", {})
    popup = named.get(key)
    if popup is None:
        return False
    is_visible = popup.isVisible() if hasattr(popup, "isVisible") else True
    if is_visible:
        if hasattr(popup, "close"):
            popup.close()
        named.pop(key, None)
        window._dnd_named_popups = named  # noqa: SLF001
        _set_status(window, status_message)
        return True
    named.pop(key, None)
    window._dnd_named_popups = named  # noqa: SLF001
    return False


def _apply_color_scheme(window, scheme: str) -> None:
    styles = {
        "Dark": dark_theme_stylesheet,
        "Parchment": parchment_theme_stylesheet,
        "High Contrast": high_contrast_theme_stylesheet,
    }
    stylesheet = styles.get(scheme, dark_theme_stylesheet)()
    if hasattr(window, "setStyleSheet"):
        window.setStyleSheet(stylesheet)
    window._dnd_color_scheme = scheme  # noqa: SLF001
    _set_status(window, f"Color scheme set to {scheme}.")


def _key_bind_rows() -> tuple[tuple[str, str], ...]:
    rows = [
        ("Action Bar Slot 1", "1"),
        ("Action Bar Slot 2", "2"),
        ("Action Bar Slot 3", "3"),
        ("Action Bar Slot 4", "4"),
        ("Action Bar Slot 5", "5"),
        ("Action Bar Slot 6", "6"),
        ("Action Bar Slot 7", "7"),
        ("Action Bar Slot 8", "8"),
        ("Action Bar Slot 9", "9"),
        ("Action Bar Slot 10", "0"),
        ("Action Bar Slot 11", "-"),
        ("Action Bar Slot 12", "="),
        ("Inventory", "B"),
        ("Spellbook", "K"),
        ("Abilities", "N"),
        ("Roll Previous Die", "Ctrl+R"),
        ("Exit", "Ctrl+Q"),
    ]
    return tuple(rows)


def _dice_notation_from_action(action_id: str) -> str | None:
    die = action_id.removeprefix("dice.roll_")
    if die in {"d4", "d6", "d8", "d10", "d12", "d20", "d100"}:
        return f"1{die}"
    return None


def _roll_menu_die(
    window,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    notation: str,
) -> str:
    result = app.dice.roll(notation)
    state.last_dice_notation = notation
    die = notation.removeprefix("1")
    message = f"{die} roll: {result.total} rolls={result.rolls}"
    _append_workspace(window, message)
    _set_status(window, message)
    return message


def _consume_inventory_item(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    character_id: str,
    item_id: str,
) -> object:
    try:
        character = app.characters.load(character_id)
    except KeyError:
        message = f"Selected character {character_id} could not be loaded."
        _set_status(window, message)
        return message
    item = next((carried for carried in character.inventory if carried.item_id == item_id), None)
    if item is None:
        message = f"{character.name} does not have {item_id}."
    elif item.category != ItemCategory.CONSUMABLE:
        message = f"{item.name} is not consumable."
    else:
        message = _consume_known_item(app, character, item)
        app.inventory.remove_item(character, item.item_id, 1, autosave=True)
    _append_workspace(window, message)
    _record_campaign_activity(app, state, str(message), "inventory")
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, message)
    try:
        updated = app.characters.load(character_id)
    except KeyError:
        return 0
    return app.inventory.quantity(updated, item_id)


def _change_character_currency(
    window,
    app: DnDCombatEngineApp,
    character_id: str,
    delta_cp: int,
):
    character = app.characters.load(character_id)
    try:
        character.currency = character.currency.add_cp(delta_cp)
    except ValueError:
        _set_status(window, "Not enough currency for that withdrawal.")
        raise
    app.characters.save(character)
    action = "Deposited" if delta_cp >= 0 else "Withdrew"
    message = f"{action} {_currency_change_text(abs(delta_cp))} for {character.name}."
    _append_workspace(window, message)
    state = getattr(window, "_dnd_campaign_state", None)
    if state is not None:
        _record_campaign_activity(app, state, message, "currency")
    _set_status(window, message)
    return character.currency


def _currency_change_text(amount_cp: int) -> str:
    pp, remainder = divmod(amount_cp, 1000)
    gp, remainder = divmod(remainder, 100)
    sp, cp = divmod(remainder, 10)
    parts = []
    for label, value in (("PP", pp), ("GP", gp), ("SP", sp), ("CP", cp)):
        if value:
            parts.append(f"{value}{label}")
    return " ".join(parts) if parts else "0CP"


def _consume_known_item(
    app: DnDCombatEngineApp,
    character: Character,
    item: InventoryItem,
) -> str:
    healing_notation = _healing_potion_notation(item)
    if healing_notation is None:
        return f"{character.name} consumes {item.name}."
    result = app.dice.roll(healing_notation)
    healed = character.hit_points.heal(result.total)
    return (
        f"{character.name} consumes {item.name}. "
        f"You regain {result.notation} Hit Points: {result.total} rolls={result.rolls}. "
        f"Healed {healed}; HP {character.hit_points.current}/{character.hit_points.maximum}."
    )


def _healing_potion_notation(item: InventoryItem) -> str | None:
    item_name = item.name.lower()
    if "potion of healing" not in item_name:
        return None
    if "supreme" in item_name:
        return "10d4+20"
    if "superior" in item_name:
        return "8d4+8"
    if "greater" in item_name:
        return "4d4+4"
    return "2d4+2"


def _break_concentration_from_menu(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    if state.concentration_spell_id is None:
        _set_status(window, "No concentration spell is active.")
        return
    spell_name = _spell_name(app, state.concentration_spell_id)
    previous = state.active_concentration
    _clear_concentration(state)
    message = _concentration_broken_message(app, previous, spell_name)
    _persist_campaign_concentration(app, state, message, "concentration")
    _refresh_campaign_docks(window, qt, app, state)
    _append_workspace(window, message)
    _set_status(window, f"Concentration broken: {spell_name}.")


def _activate_action_bar_slot(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    session: ActionBarSession,
    slot: int,
    shift_pressed: bool,
) -> str:
    if shift_pressed:
        result = app.dice.roll("1d20")
        message = f"Slot {slot} d20: {result.total} rolls={result.rolls}"
    else:
        button = session.bar.button_at(slot)
        message = _activate_action_button(app, state, button, window=window, qt=qt)
    _append_workspace(window, message)
    _record_campaign_activity(app, state, message, "action")
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, message)
    return message


def _activate_action_button(
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    button: ActionBarButton | None,
    window=None,
    qt=None,
) -> str:
    if button is None:
        return "Action slot is empty."
    character_id = _active_character_id(state)
    if character_id is None:
        return f"Select a party leader or character before using {button.name}."
    try:
        character = app.characters.load(character_id)
    except KeyError:
        return f"Selected character {character_id} could not be loaded."
    if button.kind == ActionBarActionKind.SPELL:
        return _activate_spell_button(app, character, button, state=state, window=window, qt=qt)
    return _activate_ability_button(app, character, button, state=state)


def _activate_spell_button(
    app: DnDCombatEngineApp,
    character: Character,
    button: ActionBarButton,
    state: GuiCampaignState | None = None,
    window=None,
    qt=None,
) -> str:
    try:
        spell = app.compendium.load_spell(button.action_id)
    except KeyError:
        return f"{button.name} is not in the spell compendium."
    if ensure_spell_slot_resources(character):
        app.characters.save(character)
    effect = _primary_spell_effect(spell)
    slot_message = "No spell slot used."
    slot_level = max(spell.level, button.rank) if spell.level > 0 else 0
    resource_name = _spell_resource_name(effect, spell, slot_level)
    spell_slot_resource = character.resources.get(resource_name) if resource_name else None
    if resource_name is not None:
        if spell_slot_resource is None:
            return f"{character.name} cannot cast {spell.name}: no level {slot_level} slots."
        if spell_slot_resource.current < 1:
            return (
                f"{character.name} cannot cast {spell.name}: "
                f"no level {slot_level} slots remaining."
            )
    selected_targets = _choose_spell_effect_targets(
        app,
        character,
        spell,
        effect,
        state,
        window,
        qt,
        slot_level,
    )
    if effect.requires_target and not selected_targets:
        return f"{character.name} holds {spell.name}; no target selected."
    special_target = selected_targets[0] if selected_targets else None
    special_choice: str | None = None
    if effect.effect_id == "lesser-restoration-condition":
        special_choice = _choose_lesser_restoration_effect(qt, window)
        if special_choice is None:
            return f"{character.name} holds Lesser Restoration; no effect selected."
    elif effect.target_profile == TargetProfile.SPECIAL:
        special_choice = _choose_thaumaturgy_effect(qt, window)
        if special_choice is None:
            return f"{character.name} holds {spell.name}; no effect selected."
    runtime_effect = replace(effect, resource_cost=resource_name)
    _resolve_gui_combat_action(
        app,
        character,
        runtime_effect,
        targets=_target_references_for_character_ids(app, selected_targets),
        state=state,
        concentration_effect_id=spell.spell_id if runtime_effect.starts_concentration else None,
        concentration_target_ids=selected_targets,
        concentration_name=spell.name,
    )
    if spell_slot_resource is not None:
        slot_message = (
            f"Used level {slot_level} spell slot; "
            f"{spell_slot_resource.current}/{spell_slot_resource.maximum} remain."
        )
    if effect.effect_id == "beacon-of-hope-buff":
        target_text = ", ".join(_character_names(app, selected_targets))
        return (
            f"{character.name} casts {spell.name} on {target_text}. "
            f"Hope and Vitality applied while concentration holds. {slot_message}"
        )
    if effect.effect_id == "bless-buff":
        target_text = ", ".join(_character_names(app, selected_targets))
        return (
            f"{character.name} casts {spell.name} on {target_text}. "
            f"Targets add {effect.dice or '1d4'} to attack rolls and saving throws "
            f"while concentration holds. {slot_message}"
        )
    if effect.effect_id == "cure-wounds-healing" and special_target is not None:
        return _apply_cure_wounds(app, character, special_target, slot_level, slot_message)
    if effect.effect_id == "lesser-restoration-condition" and special_target is not None:
        return _apply_lesser_restoration(
            app,
            character,
            special_target,
            special_choice or "",
            slot_message,
        )
    if effect.effect_id == "light-utility" and special_target is not None:
        target_name = _character_name(app, special_target)
        return (
            f"{character.name} casts {spell.name} for {target_name}. "
            "A touched object sheds bright light in a 20-foot radius and dim light for "
            f"another 20 feet for 1 hour. {slot_message}"
        )
    if effect.effect_id == "revivify-healing" and special_target is not None:
        return _apply_revivify(app, character, special_target, slot_message)
    if effect.effect_id == "thaumaturgy-utility" and special_choice is not None:
        return (
            f"{character.name} casts {spell.name}. {special_choice} "
            f"The divine sign lingers for {effect.duration.text or spell.duration}. {slot_message}"
        )
    damage_message, damage_total = _roll_spell_effect_damage(app, spell.damage, effect)
    target = _active_target_for_effect(app, state)
    if target is not None and damage_total > 0 and effect.effect_kind == EffectKind.DAMAGE:
        applied = _apply_damage_to_target(app, target, damage_total)
        resolution = EffectResolution(
            source_name=character.name,
            effect_name=spell.name,
            effect_kind=effect.effect_kind,
            target=target,
            total=damage_total,
            detail=f"{damage_message} {applied} {slot_message}",
        )
        return resolution.message()
    return f"{character.name} casts {spell.name}. {damage_message} {slot_message}"


def _primary_spell_effect(spell) -> EffectDefinition:
    if spell.effects:
        return spell.effects[0]
    return _legacy_spell_effect(spell)


def _legacy_spell_effect(spell) -> EffectDefinition:
    legacy = {
        "beacon_of_hope": (
            "beacon-of-hope-buff",
            EffectKind.BUFF,
            TargetProfile.MULTIPLE_CREATURES,
            "spell_slot_3",
            None,
        ),
        "bless": (
            "bless-buff",
            EffectKind.BUFF,
            TargetProfile.MULTIPLE_CREATURES,
            "spell_slot_1",
            "1d4",
        ),
        "cure_wounds": (
            "cure-wounds-healing",
            EffectKind.HEALING,
            TargetProfile.ONE_CREATURE,
            "spell_slot_1",
            "1d8+spellcasting_modifier",
        ),
        "lesser_restoration": (
            "lesser-restoration-condition",
            EffectKind.CONDITION,
            TargetProfile.ONE_CREATURE,
            "spell_slot_2",
            None,
        ),
        "light": (
            "light-utility",
            EffectKind.UTILITY,
            TargetProfile.OBJECT,
            None,
            None,
        ),
        "revivify": (
            "revivify-healing",
            EffectKind.HEALING,
            TargetProfile.ONE_CREATURE,
            "spell_slot_3",
            "1",
        ),
        "thaumaturgy": (
            "thaumaturgy-utility",
            EffectKind.UTILITY,
            TargetProfile.SPECIAL,
            None,
            None,
        ),
    }
    default = (
        f"{spell.spell_id}-effect",
        EffectKind.DAMAGE if spell.damage is not None else EffectKind.UTILITY,
        TargetProfile.ONE_CREATURE if spell.damage is not None else TargetProfile.SPECIAL,
        "spell_slot_1" if spell.level > 0 else None,
        None,
    )
    effect_id, effect_kind, target_profile, resource_cost, dice = legacy.get(
        spell.spell_id,
        default,
    )
    duration_kind = "concentration" if spell.concentration else "instantaneous"
    duration_text = "up to 1 minute" if spell.spell_id == "thaumaturgy" else spell.duration
    return EffectDefinition.from_dict(
        {
            "effect_id": effect_id,
            "name": spell.name,
            "effect_kind": effect_kind.value,
            "target_profile": target_profile.value,
            "action_cost": "action",
            "range_text": spell.range_text,
            "duration": {
                "kind": duration_kind,
                "amount": None,
                "text": duration_text,
            },
            "check": {
                "kind": "saving_throw" if spell.saving_throw else "none",
                "ability": spell.saving_throw,
                "dc": None,
                "bonus": 0,
                "proficiency_applies": False,
            },
            "resource_cost": resource_cost,
            "dice": dice,
            "rule_source": None,
        }
    )


def _spell_resource_name(
    effect: EffectDefinition,
    spell,
    slot_level: int,
) -> str | None:
    if effect.resource_cost is None:
        return None
    if effect.resource_cost.startswith("spell_slot_"):
        return f"spell_slot_{slot_level or spell.level}"
    return effect.resource_cost


def _resolve_gui_combat_action(
    app: DnDCombatEngineApp,
    character: Character,
    effect: EffectDefinition,
    *,
    targets: tuple[TargetReference, ...] = (),
    total: int | None = None,
    detail: str = "",
    state: GuiCampaignState | None = None,
    concentration_effect_id: str | None = None,
    concentration_target_ids: tuple[str, ...] = (),
    concentration_name: str | None = None,
):
    """Resolve one GUI action through the shared controller loop and persist side effects."""
    request = CombatActionRequest(
        actor_id=character.character_id,
        actor_name=character.name,
        action=effect,
        targets=targets,
        total=total,
        detail=detail,
        resources=character.resources,
    )
    combat = getattr(app, "combat", None)
    if combat is not None and hasattr(combat, "execute_action"):
        resolution = combat.execute_action(request).resolution
    else:
        resolution = EffectResolver().resolve(
            EffectPlan(
                actor_name=request.actor_name,
                definition=request.action,
                targets=request.targets,
                total=request.total,
                detail=request.detail,
            ),
            resources=request.resources,
        )
    if resolution.resource_spent is not None:
        app.characters.save(character)
    if concentration_effect_id is not None and state is not None:
        _set_concentration(
            state,
            character.character_id,
            concentration_effect_id,
            concentration_target_ids,
            concentration_name,
        )
        _persist_campaign_concentration(app, state)
    return resolution


def _target_references_for_character_ids(
    app: DnDCombatEngineApp,
    character_ids: tuple[str, ...],
) -> tuple[TargetReference, ...]:
    return tuple(_character_target_reference_with_name(app, item) for item in character_ids)


def _character_target_reference_with_name(
    app: DnDCombatEngineApp,
    character_id: str,
) -> TargetReference:
    return TargetReference(
        target_id=character_id,
        name=_character_name(app, character_id),
        kind=TargetKind.CHARACTER,
        source_id=character_id,
    )


def _choose_spell_effect_targets(
    app: DnDCombatEngineApp,
    character: Character,
    spell,
    effect: EffectDefinition,
    state: GuiCampaignState | None,
    window,
    qt,
    slot_level: int,
) -> tuple[str, ...]:
    if effect.effect_id == "beacon-of-hope-buff":
        return _choose_beacon_targets(qt, window, app, state, character)
    if effect.effect_id == "bless-buff":
        return _choose_bless_targets(qt, window, app, state, character, slot_level)
    if effect.target_profile in {TargetProfile.ONE_CREATURE, TargetProfile.OBJECT}:
        target = _active_character_target_id(app, state)
        if target is None:
            target = _choose_single_party_target(
                qt,
                window,
                app,
                state,
                character,
                f"{spell.name} Target",
                f"Choose a target for {spell.name}:",
            )
        return (target,) if target is not None else ()
    return ()


def _roll_spell_effect_damage(
    app: DnDCombatEngineApp,
    damage: DamageProfile | None,
    effect: EffectDefinition,
) -> tuple[str, int]:
    if damage is not None:
        return _roll_damage_profile(app, damage)
    if effect.effect_kind != EffectKind.DAMAGE or effect.dice is None:
        return "No damage dice configured.", 0
    result = app.dice.roll(effect.dice)
    return f"Damage {result.total} ({result.notation}: rolls={result.rolls}).", result.total


def _choose_beacon_targets(
    qt,
    parent,
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
    caster: Character,
) -> tuple[str, ...]:
    return _choose_party_targets(
        qt,
        parent,
        app,
        state,
        caster,
        "Beacon of Hope Targets",
        "Choose party members in range:",
    )


def _choose_bless_targets(
    qt,
    parent,
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
    caster: Character,
    slot_level: int,
) -> tuple[str, ...]:
    max_targets = 3 + max(0, slot_level - 1)
    return _choose_party_targets(
        qt,
        parent,
        app,
        state,
        caster,
        "Bless Targets",
        f"Choose up to {max_targets} creatures in range:",
        max_targets=max_targets,
    )


def _choose_single_party_target(
    qt,
    parent,
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
    caster: Character,
    title: str,
    prompt: str,
) -> str | None:
    selected = _choose_party_targets(
        qt,
        parent,
        app,
        state,
        caster,
        title,
        prompt,
        max_targets=1,
    )
    return selected[0] if selected else None


def _choose_party_targets(
    qt,
    parent,
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
    caster: Character,
    title: str,
    prompt: str,
    max_targets: int | None = None,
) -> tuple[str, ...]:
    target_ids = _beacon_candidate_ids(app, state, caster)
    if qt is None or parent is None:
        return target_ids[:max_targets] if max_targets is not None else target_ids
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    checkbox_class = getattr(qt.QtWidgets, "QCheckBox", None)
    button_box_class = getattr(qt.QtWidgets, "QDialogButtonBox", None)
    if dialog_class is None or checkbox_class is None or button_box_class is None:
        return target_ids[:max_targets] if max_targets is not None else target_ids
    dialog = dialog_class(parent)
    if hasattr(dialog, "setWindowTitle"):
        dialog.setWindowTitle(title)
    layout = qt.QtWidgets.QVBoxLayout(dialog)
    layout.addWidget(qt.QtWidgets.QLabel(prompt))
    checkboxes = []
    for character_id in target_ids:
        checkbox = checkbox_class(_character_name(app, character_id))
        if hasattr(checkbox, "setChecked"):
            checkbox.setChecked(True)
        layout.addWidget(checkbox)
        checkboxes.append((character_id, checkbox))
    buttons = _dialog_buttons(button_box_class)
    button_box = button_box_class(buttons) if buttons is not None else button_box_class()
    if hasattr(button_box, "accepted"):
        button_box.accepted.connect(dialog.accept)
    if hasattr(button_box, "rejected"):
        button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    result = dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()
    accepted = _dialog_accepted(dialog_class, result)
    if not accepted:
        return ()
    return tuple(
        character_id
        for character_id, checkbox in checkboxes
        if not hasattr(checkbox, "isChecked") or checkbox.isChecked()
    )[:max_targets]


def _choose_lesser_restoration_effect(qt, parent) -> str | None:
    return _choose_string(
        qt,
        parent,
        "Lesser Restoration",
        "Condition or disease:",
        ("Disease", "Blinded", "Deafened", "Paralyzed", "Poisoned"),
    )


def _choose_thaumaturgy_effect(qt, parent) -> str | None:
    return _choose_string(
        qt,
        parent,
        "Thaumaturgy",
        "Magical effect:",
        (
            "Your voice booms up to three times as loud.",
            "Flames flicker, brighten, dim, or change color.",
            "Harmless tremors shake the ground.",
            "An instantaneous sound rings from a point in range.",
            "An unlocked door or window flies open or slams shut.",
            "Your eyes alter in appearance.",
        ),
    )


def _choose_string(qt, parent, title: str, prompt: str, options: tuple[str, ...]) -> str | None:
    if qt is None or parent is None:
        return options[0] if options else None
    dialog = getattr(qt.QtWidgets, "QInputDialog", None)
    if dialog is None:
        return options[0] if options else None
    selected = dialog.getItem(parent, title, prompt, list(options), 0, False)
    if isinstance(selected, tuple):
        value, accepted = selected
        return str(value) if accepted else None
    return str(selected) if selected is not None else None


def _apply_cure_wounds(
    app: DnDCombatEngineApp,
    caster: Character,
    target_id: str,
    slot_level: int,
    slot_message: str,
) -> str:
    target = app.characters.load(target_id)
    modifier = caster.abilities.modifier("wisdom")
    notation = f"{max(1, slot_level)}d8{modifier:+d}" if modifier else f"{max(1, slot_level)}d8"
    result = app.dice.roll(notation)
    healed = target.hit_points.heal(result.total)
    app.characters.save(target)
    target_reference = TargetReference(
        target_id=target.character_id,
        name=target.name,
        kind=TargetKind.CHARACTER,
        source_id=target.character_id,
    )
    return EffectResolution(
        source_name=caster.name,
        effect_name="Cure Wounds",
        effect_kind=EffectKind.HEALING,
        target=target_reference,
        total=healed,
        detail=(
            f"Healing {result.notation}: {result.total} rolls={result.rolls}. "
            f"HP {target.hit_points.current}/{target.hit_points.maximum}. {slot_message}"
        ),
    ).message()


def _apply_lesser_restoration(
    app: DnDCombatEngineApp,
    caster: Character,
    target_id: str,
    effect: str,
    slot_message: str,
) -> str:
    target = app.characters.load(target_id)
    removed = _remove_restoration_condition(target, effect)
    app.characters.save(target)
    if removed:
        result = f"{effect.lower()} is ended"
    elif effect.lower() == "disease":
        result = "one disease is ended"
    else:
        result = f"{target.name} had no tracked {effect.lower()} condition"
    return f"{caster.name} casts Lesser Restoration on {target.name}; {result}. {slot_message}"


def _remove_restoration_condition(target: Character, effect: str) -> bool:
    normalized = effect.lower()
    if normalized == "disease":
        return False
    try:
        condition_name = ConditionName(normalized)
    except ValueError:
        return False
    before = len(target.conditions)
    target.conditions = tuple(
        condition for condition in target.conditions if condition.name != condition_name
    )
    return len(target.conditions) != before


def _apply_revivify(
    app: DnDCombatEngineApp,
    caster: Character,
    target_id: str,
    slot_message: str,
) -> str:
    target = app.characters.load(target_id)
    healed = target.hit_points.heal(1)
    app.characters.save(target)
    detail = "returns with 1 hit point" if healed else "is already above 0 hit points"
    return f"{caster.name} casts Revivify on {target.name}; {detail}. {slot_message}"


def _beacon_candidate_ids(
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
    caster: Character,
) -> tuple[str, ...]:
    if state is None or state.active_campaign_id is None:
        return (caster.character_id,)
    try:
        campaign = app.campaigns.load(state.active_campaign_id)
    except (AttributeError, KeyError):
        return (caster.character_id,)
    return campaign.character_ids or (caster.character_id,)


def _dialog_buttons(button_box_class):
    standard_button = getattr(button_box_class, "StandardButton", button_box_class)
    ok_button = getattr(standard_button, "Ok", None)
    cancel_button = getattr(standard_button, "Cancel", None)
    if ok_button is None:
        ok_button = getattr(button_box_class, "Ok", None)
    if cancel_button is None:
        cancel_button = getattr(button_box_class, "Cancel", None)
    if ok_button is not None and cancel_button is not None:
        return ok_button | cancel_button
    return None


def _dialog_accepted(dialog_class, result) -> bool:
    accepted = getattr(dialog_class, "DialogCode", dialog_class)
    accepted_value = getattr(accepted, "Accepted", None)
    if accepted_value is None:
        accepted_value = getattr(dialog_class, "Accepted", None)
    if accepted_value is None:
        accepted_value = 1
    return result == accepted_value or result is True


def _load_campaign_concentration(
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    if state.active_campaign_id is None:
        _clear_concentration(state)
        return
    try:
        campaign = app.campaigns.load(state.active_campaign_id)
    except (AttributeError, KeyError):
        return
    _apply_concentration_to_state(state, campaign.active_concentration)


def _apply_concentration_to_state(
    state: GuiCampaignState,
    concentration: ConcentrationState | None,
) -> None:
    if concentration is None:
        _clear_concentration(state)
        return
    state.active_concentration = concentration
    state.concentration_character_id = concentration.caster_id
    state.concentration_spell_id = concentration.effect_id
    target_ids = tuple(target.target_id for target in concentration.targets)
    state.beacon_of_hope_targets = (
        target_ids if concentration.effect_id == "beacon_of_hope" else ()
    )
    state.bless_targets = target_ids if concentration.effect_id == "bless" else ()


def _set_concentration(
    state: GuiCampaignState,
    character_id: str,
    spell_id: str,
    target_ids: tuple[str, ...] = (),
    spell_name: str | None = None,
) -> None:
    if state.concentration_character_id == character_id:
        _clear_concentration(state)
    state.concentration_character_id = character_id
    state.concentration_spell_id = spell_id
    state.active_concentration = ConcentrationState(
        caster_id=character_id,
        effect_id=spell_id,
        effect_name=spell_name or _spell_display_name(spell_id),
        targets=tuple(_character_target_reference(character_id) for character_id in target_ids),
    )
    if spell_id != "beacon_of_hope":
        state.beacon_of_hope_targets = ()
    else:
        state.beacon_of_hope_targets = target_ids
    if spell_id != "bless":
        state.bless_targets = ()
    else:
        state.bless_targets = target_ids


def _clear_concentration(state: GuiCampaignState) -> None:
    state.concentration_character_id = None
    state.concentration_spell_id = None
    state.active_concentration = None
    state.beacon_of_hope_targets = ()
    state.bless_targets = ()


def _persist_campaign_concentration(
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
    message: str | None = None,
    category: str = "concentration",
) -> None:
    if state is None or state.active_campaign_id is None:
        return
    try:
        campaign = app.campaigns.load(state.active_campaign_id)
    except (AttributeError, KeyError):
        return
    updated = campaign.with_concentration(state.active_concentration)
    if message:
        updated = updated.with_activity(message, category)
    try:
        app.campaigns.save(updated)
    except AttributeError:
        return


def _concentration_broken_message(
    app: DnDCombatEngineApp,
    previous: ConcentrationState | None,
    fallback_spell_name: str,
) -> str:
    if previous is None:
        return f"Concentration broken: {fallback_spell_name}."
    target_names = tuple(
        _character_name(app, target.target_id) for target in previous.targets
    )
    if not target_names:
        return f"Concentration broken: {previous.effect_name}."
    return (
        f"Concentration broken: {previous.effect_name}. "
        f"Removed {previous.effect_name} from {', '.join(target_names)}."
    )


def _character_target_reference(character_id: str) -> TargetReference:
    return TargetReference(
        target_id=character_id,
        name=character_id,
        kind=TargetKind.CHARACTER,
        source_id=character_id,
    )


def _spell_display_name(spell_id: str) -> str:
    return spell_id.replace("_", " ").title()


def _character_names(app: DnDCombatEngineApp, character_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_character_name(app, character_id) for character_id in character_ids)


def _character_name(app: DnDCombatEngineApp, character_id: str) -> str:
    try:
        return app.characters.load(character_id).name
    except KeyError:
        return character_id


def _spell_name(app: DnDCombatEngineApp, spell_id: str) -> str:
    try:
        return app.compendium.load_spell(spell_id).name
    except KeyError:
        return spell_id


def _activate_ability_button(
    app: DnDCombatEngineApp,
    character: Character,
    button: ActionBarButton,
    state: GuiCampaignState | None = None,
) -> str:
    if not _ability_uses_weapon_damage(character, button):
        return f"{button.name} is character sheet information, not a configured combat action."
    if button.name.lower() == "unarmed strike" or button.action_id == "unarmed_strike":
        damage = max(1 + character.abilities.modifier("strength"), 1)
        target = _active_target_for_effect(app, state)
        if target is not None:
            applied = _apply_damage_to_target(app, target, damage)
            _resolve_gui_combat_action(
                app,
                character,
                _action_effect_definition("unarmed-attack", "Unarmed Strike"),
                targets=(target,),
                total=damage,
                detail=f"Damage {damage} bludgeoning. {applied}",
                state=state,
            )
            return EffectResolution(
                source_name=character.name,
                effect_name="Unarmed Strike",
                effect_kind=EffectKind.ATTACK,
                target=target,
                total=damage,
                detail=f"Damage {damage} bludgeoning. {applied}",
            ).message()
        return (
            f"{character.name} uses Unarmed Strike rank {button.rank}. "
            f"Damage {damage} bludgeoning."
        )
    weapon = _weapon_for_button(character, button)
    if weapon is None:
        return f"{character.name} uses {button.name}. No attack damage dice configured."
    damage_message, damage_total = _roll_damage_profile(app, weapon.damage)
    target = _active_target_for_effect(app, state)
    if target is not None:
        applied = _apply_damage_to_target(app, target, damage_total)
        _resolve_gui_combat_action(
            app,
            character,
            _action_effect_definition(button.action_id, button.name),
            targets=(target,),
            total=damage_total,
            detail=f"{damage_message} {applied}",
            state=state,
        )
        return EffectResolution(
            source_name=character.name,
            effect_name=f"{button.name} with {weapon.name}",
            effect_kind=EffectKind.ATTACK,
            target=target,
            total=damage_total,
            detail=f"{damage_message} {applied}",
        ).message()
    return (
        f"{character.name} uses {button.name} with {weapon.name} "
        f"rank {button.rank}. {damage_message}"
    )


def _action_effect_definition(action_id: str, name: str) -> EffectDefinition:
    return EffectDefinition.from_dict(
        {
            "effect_id": _action_identifier(action_id) or "action",
            "name": name,
            "effect_kind": "attack",
            "target_profile": "one_creature",
            "action_cost": "action",
            "range_text": "",
            "duration": {
                "kind": "instantaneous",
                "amount": None,
                "text": "Instantaneous",
            },
            "check": {
                "kind": "attack_roll",
                "ability": "strength",
                "dc": None,
                "bonus": 0,
                "proficiency_applies": True,
            },
            "resource_cost": None,
            "dice": None,
            "rule_source": None,
        }
    )


def _weapon_for_button(character: Character, button: ActionBarButton):
    action_id = button.action_id.lower()
    name = button.name.lower()
    for weapon in character.weapons:
        if _action_identifier(weapon.name) == action_id or weapon.name.lower() == name:
            return weapon
    return character.weapons[0] if character.weapons else None


def _ability_uses_weapon_damage(character: Character, button: ActionBarButton) -> bool:
    action_id = button.action_id.lower()
    name = button.name.lower()
    weapon_actions = {
        "attack",
        "basic_attack",
        "sneak_attack",
        "great_weapon_master",
        "sharpshooter",
        "divine_smite",
        "rage",
        "unarmed_strike",
    }
    weapon_actions.update(_action_identifier(weapon.name) for weapon in character.weapons)
    return action_id in weapon_actions or name in {
        "attack",
        "basic attack",
        "sneak attack",
        "great weapon master",
        "sharpshooter",
        "divine smite",
        "rage",
        "unarmed strike",
    } or name in {weapon.name.lower() for weapon in character.weapons}


def _action_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _roll_damage_profile(app: DnDCombatEngineApp, damage: DamageProfile | None) -> tuple[str, int]:
    if damage is None:
        return "No damage dice configured.", 0
    parts = []
    total = 0
    for component in damage.components:
        result = app.dice.roll(component.dice)
        total += result.total
        parts.append(
            f"{result.notation} {component.damage_type.value}: "
            f"{result.total} rolls={result.rolls}"
        )
    return f"Damage {total} ({'; '.join(parts)}).", total


def _active_target_for_effect(
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
) -> TargetReference | None:
    if state is None or state.active_target is None:
        return None
    target = state.active_target
    if target.kind is TargetKind.CHARACTER:
        try:
            character = app.characters.load(target.source_id)
        except KeyError:
            return None
        return TargetReference(
            target_id=character.character_id,
            name=character.name,
            kind=TargetKind.CHARACTER,
            source_id=character.character_id,
        )
    if target.kind is TargetKind.MONSTER:
        try:
            monster = app.compendium.load_monster(target.source_id)
        except KeyError:
            return None
        return TargetReference(
            target_id=target.target_id,
            name=monster.name,
            kind=TargetKind.MONSTER,
            source_id=monster.monster_id,
        )
    return target


def _active_character_target_id(
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
) -> str | None:
    target = _active_target_for_effect(app, state)
    if target is None or target.kind is not TargetKind.CHARACTER:
        return None
    return target.source_id


def _apply_damage_to_target(
    app: DnDCombatEngineApp,
    target: TargetReference,
    damage_total: int,
) -> str:
    if target.kind is TargetKind.MONSTER:
        return _apply_damage_to_monster_target(app, target, damage_total)
    character = app.characters.load(target.source_id)
    dealt = character.hit_points.apply_damage(damage_total)
    app.characters.save(character)
    return (
        f"Applied {dealt} damage; HP "
        f"{character.hit_points.current}/{character.hit_points.maximum}."
    )


def _apply_damage_to_monster_target(
    app: DnDCombatEngineApp,
    target: TargetReference,
    damage_total: int,
) -> str:
    try:
        encounter_ids = app.encounters.persistence_service.list_encounter_ids()
    except AttributeError:
        return "Encounter target HP tracking is unavailable."
    for encounter_id in encounter_ids:
        try:
            encounter = app.encounters.load(encounter_id)
        except KeyError:
            continue
        for participant in encounter.participants:
            if (
                participant.kind is ParticipantKind.MONSTER
                or getattr(participant.kind, "value", None) == ParticipantKind.MONSTER.value
            ) and (
                participant.participant_id == target.target_id
                and participant.source_id == target.source_id
            ):
                monster = app.compendium.load_monster(participant.source_id)
                maximum_hp = monster.hit_points.maximum * participant.quantity
                updated_participant, dealt = participant.apply_damage(damage_total, maximum_hp)
                app.encounters.save(encounter.with_participant(updated_participant))
                return (
                    f"Applied {dealt} damage; HP "
                    f"{updated_participant.current_hit_points}/{maximum_hp}."
                )
    return "Encounter target could not be found."


def _roll_saving_throw(
    window,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    ability: str,
) -> str:
    character_id = _active_character_id(state)
    if character_id is None:
        message = "No party leader selected for saving throw."
        _set_status(window, message)
        return message
    try:
        character = app.characters.load(character_id)
    except KeyError:
        message = f"Party leader {character_id} could not be loaded."
        _set_status(window, message)
        return message
    modifier = character.abilities.modifier(ability)  # type: ignore[arg-type]
    proficient = ability.lower() in {
        name.lower() for name in character.saving_throw_proficiencies
    }
    proficiency = _proficiency_bonus(character.level) if proficient else 0
    result = app.dice.roll("1d20")
    total = result.total + modifier + proficiency
    message = (
        f"{character.name} {ability.title()} save: {total} "
        f"(d20 {result.total} rolls={result.rolls}, modifier {modifier:+d}"
        f"{', proficiency +' + str(proficiency) if proficient else ''})."
    )
    _append_workspace(window, message)
    _set_status(window, message)
    return message


def _proficiency_bonus(level: int) -> int:
    return 2 + max(level - 1, 0) // 4


def _append_workspace(window, message: str) -> None:
    workspace = getattr(window, "_dnd_central", None)
    if workspace is None:
        return
    if hasattr(workspace, "append"):
        workspace.append(message)
        return
    if hasattr(workspace, "setText"):
        workspace.setText(message)


def _record_campaign_activity(
    app: DnDCombatEngineApp,
    state: GuiCampaignState | None,
    message: str,
    category: str = "system",
) -> None:
    if state is None or state.active_campaign_id is None or not message:
        return
    try:
        campaign = app.campaigns.load(state.active_campaign_id)
    except (AttributeError, KeyError):
        return
    try:
        app.campaigns.save(campaign.with_activity(message, category))
    except AttributeError:
        return


def _replace_dock_widget(docks: dict[str, object], title: str, widget) -> None:
    dock = docks.get(title)
    if dock is not None and hasattr(dock, "setWidget"):
        dock.setWidget(widget)


def _replace_panel_widget(panels: dict[str, object], title: str, widget) -> None:
    host = panels.get(title)
    if host is None:
        return
    layout = getattr(host, "_dnd_panel_layout", None)
    old_widget = getattr(host, "_dnd_panel_widget", None)
    if layout is not None:
        if old_widget is not None and hasattr(layout, "removeWidget"):
            layout.removeWidget(old_widget)
        _layout_add_widget(layout, widget)
    if old_widget is not None and hasattr(old_widget, "setParent"):
        old_widget.setParent(None)
    host._dnd_panel_widget = widget  # noqa: SLF001


def _campaign_widget(app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    if state.active_campaign_id is None:
        return _label(qt, "No campaign open")
    return CampaignWidget.create(app, qt, state.active_campaign_id)


def _activity_widget(app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    return CampaignActivityWidget.create(app, qt, state.active_campaign_id)


def _party_widget(window, app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    if state.active_campaign_id is None:
        return _label(qt, "No campaign open")
    return PartyFramesWidget.create(
        app,
        qt,
        state.active_campaign_id,
        initiative_results=state.party_initiative,
        beacon_of_hope_targets=state.beacon_of_hope_targets,
        bless_targets=state.bless_targets,
        on_upload_sheet=lambda character_id, source_kind: _replace_party_member_sheet(
            window,
            qt,
            app,
            state,
            character_id,
            source_kind,
        ),
        on_remove_member=lambda character_id: _remove_party_member(
            window,
            qt,
            app,
            state,
            character_id,
        ),
        on_set_initiative=lambda character_id, value: _set_party_initiative(
            window,
            qt,
            app,
            state,
            character_id,
            value,
        ),
    )


def _target_widget(window, app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    return TargetPanelWidget.create(
        app,
        qt,
        state.active_campaign_id,
        active_target=state.active_target,
        on_select=lambda target: _set_active_target(window, qt, app, state, target),
    )


def _set_active_target(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    target: TargetReference,
) -> None:
    state.active_target = target
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Target selected: {target.name}.")


def _replace_party_member_sheet(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    character_id: str,
    source_kind: str = "pdf",
) -> None:
    try:
        if source_kind == "url":
            url = ask_character_url(qt, window)
            if not url:
                _set_status(window, "Character URL import canceled.")
                return
            draft = app.character_imports.preview_url(url)
        else:
            path = choose_character_pdf(qt, window)
            if not path:
                _set_status(window, "Character PDF import canceled.")
                return
            draft = app.character_imports.preview_pdf(path)
        reviewed = review_character_import(qt, window, draft)
        if reviewed is None:
            _set_status(window, "Character sheet update canceled.")
            return
        app.characters.save(reviewed.to_character(character_id))
    except ValueError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    except KeyError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    state.selected_character_id = character_id
    if (
        state.active_target is not None
        and state.active_target.kind is TargetKind.CHARACTER
        and state.active_target.source_id == character_id
    ):
        state.active_target = TargetReference(
            target_id=character_id,
            name=reviewed.name,
            kind=TargetKind.CHARACTER,
            source_id=character_id,
        )
    _refresh_campaign_docks(window, qt, app, state)
    _show_message(window, qt, "Character Sheet Updated", f"Updated {reviewed.name}.")


def _remove_party_member(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    character_id: str,
) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Remove Failed", "Open or create a campaign first.", error=True)
        return
    try:
        campaign = app.campaigns.load(state.active_campaign_id).without_character(character_id)
        app.campaigns.save(campaign)
    except KeyError as exc:
        _show_message(window, qt, "Remove Failed", str(exc), error=True)
        return
    state.party_initiative.pop(character_id, None)
    if state.selected_character_id == character_id:
        state.selected_character_id = campaign.character_ids[0] if campaign.character_ids else None
    if state.party_leader_character_id == character_id:
        state.party_leader_character_id = (
            campaign.character_ids[0] if campaign.character_ids else None
        )
    if (
        state.active_target is not None
        and state.active_target.kind is TargetKind.CHARACTER
        and state.active_target.source_id == character_id
    ):
        state.active_target = None
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Removed {character_id} from party.")


def _set_party_initiative(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    character_id: str,
    value: int,
) -> None:
    state.party_initiative[character_id] = value
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Set {character_id} initiative to {value}.")


def _campaign_editor_widget(app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    if state.active_campaign_id is None:
        return _label(qt, "Open or begin a campaign to edit references.")
    return CampaignEditorWidget.create(app, qt, state.active_campaign_id)


def _character_widget(app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    if state.selected_character_id is None:
        return _label(qt, "No character selected")
    return CharacterSheetWidget.create(app, qt, state.selected_character_id)


def _spellbook_widget(
    app: DnDCombatEngineApp,
    qt,
    state: GuiCampaignState,
    session: ActionBarSession,
):
    return SpellbookWidget.create(app, qt, session, _active_character_id(state))


def _abilities_widget(
    app: DnDCombatEngineApp,
    qt,
    state: GuiCampaignState,
    session: ActionBarSession,
):
    character_id = _active_character_id(state)
    if character_id is None:
        return _label(qt, "No party leader selected")
    return AbilitiesWidget.create(app, qt, session, character_id)


def _action_bar_widget(
    app: DnDCombatEngineApp,
    qt,
    state: GuiCampaignState,
    session: ActionBarSession,
    on_activate,
    on_save=None,
):
    widget = qt.QtWidgets.QWidget()
    layout = qt.QtWidgets.QHBoxLayout(widget)
    _layout_add_widget(layout, SpellSlotTrackerWidget.create(app, qt, _active_character_id(state)))
    _layout_add_widget(
        layout,
        ActionBarWidget.create(qt, session, on_activate=on_activate, app=app),
        1,
    )
    saving_throw_widget = SavingThrowWidget.create(
        app,
        qt,
        _active_character_id(state),
        on_roll=on_save,
    )
    if saving_throw_widget is not None:
        _layout_add_widget(layout, saving_throw_widget)
    return widget


def _active_character_id(state: GuiCampaignState) -> str | None:
    return state.party_leader_character_id or state.selected_character_id


def _label(qt, text: str):
    widget = qt.QtWidgets.QLabel(text)
    widget.setAlignment(qt.QtCore.Qt.AlignmentFlag.AlignCenter)
    return widget


def _central_text(app: DnDCombatEngineApp, state: GuiCampaignState) -> str:
    if state.active_campaign_id is None:
        return "No campaign open"
    return "Combat Workspace"


def _unique_campaign_id(app: DnDCombatEngineApp, name: str) -> str:
    base = _slug(name) or "campaign"
    existing = set(app.campaigns.list_ids())
    if base not in existing:
        return base
    counter = 2
    while f"{base}_{counter}" in existing:
        counter += 1
    return f"{base}_{counter}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


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

