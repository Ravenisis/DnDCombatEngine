"""Main GUI window."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp, create_app
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.gui.actions import action_specs_by_menu, default_action_specs
from dnd_combat_engine.gui.import_dialogs import (
    ask_campaign_name,
    ask_character_url,
    choose_character_pdf,
)
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
    PartyFramesWidget,
    SpellbookWidget,
)
from dnd_combat_engine.models import ActionBarActionKind, ActionBarButton, Campaign, Character
from dnd_combat_engine.models.damage import DamageProfile


@dataclass(slots=True)
class GuiCampaignState:
    """Mutable GUI state for the currently open campaign workspace."""

    active_campaign_id: str | None = "starter_campaign"
    selected_character_id: str | None = "vale"
    party_initiative: dict[str, int] = field(default_factory=dict)


def create_main_window(app: DnDCombatEngineApp | None = None):
    """Create the main application window."""
    qt = load_qt()
    application = app or create_app(Path("data"))
    session = GuiSession()
    window = qt.QtWidgets.QMainWindow()
    action_bar_session = ActionBarSession()
    campaign_state = GuiCampaignState()
    window.setWindowTitle("DnDCombatEngine")
    window.resize(session.window_width, session.window_height)
    window.setStyleSheet(dark_theme_stylesheet())
    if hasattr(window, "setDockNestingEnabled"):
        window.setDockNestingEnabled(True)

    central = qt.QtWidgets.QTextEdit()
    central.setReadOnly(True)
    central.append("Combat Workspace")
    window.setCentralWidget(central)
    window._dnd_central = central  # noqa: SLF001
    window._dnd_docks = {}  # noqa: SLF001

    _add_dock(window, qt, "Campaign", _campaign_widget(application, qt, campaign_state))
    _add_dock(window, qt, "Party", _party_widget(window, application, qt, campaign_state))
    _add_dock(
        window,
        qt,
        "Campaign Editor",
        _campaign_editor_widget(application, qt, campaign_state),
    )
    _add_dock(window, qt, "Character Sheet", _character_widget(application, qt, campaign_state))
    _add_dock(window, qt, "Combat Log", CombatLogWidget.create(qt))
    _add_dock(window, qt, "Dice Tray", DiceTrayWidget.create(application, qt))
    _add_dock(window, qt, "Encounter", EncounterTrackerWidget.create(application, qt))
    _add_dock(window, qt, "Encounter Editor", EncounterEditorWidget.create(application, qt))
    _add_dock(window, qt, "Attack", AttackPanelWidget.create(application, qt))
    _add_dock(window, qt, "Spellbook", SpellbookWidget.create(application, qt, action_bar_session))
    _add_dock(window, qt, "Abilities", AbilitiesWidget.create(application, qt, action_bar_session))
    _add_bottom_dock(
        window,
        qt,
        "Action Bar",
        ActionBarWidget.create(
            qt,
            action_bar_session,
            on_activate=lambda slot, shift_pressed: _activate_action_bar_slot(
                window,
                qt,
                application,
                campaign_state,
                action_bar_session,
                slot,
                shift_pressed,
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
    if action_id == "campaign.import_pdf":
        _import_pdf_from_menu(window, qt, app, state)
        return
    if action_id == "campaign.import_url":
        _import_url_from_menu(window, qt, app, state)
        return
    _set_status(window, f"{action_id} selected.")


def _import_pdf_from_menu(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Import Failed", "Open or create a campaign first.", error=True)
        return
    path = choose_character_pdf(qt, window)
    if not path:
        _set_status(window, "Character PDF import canceled.")
        return
    _run_import_result(
        window,
        qt,
        app,
        state,
        lambda: app.character_imports.import_pdf_to_campaign(path, state.active_campaign_id or ""),
    )


def _import_url_from_menu(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
    if state.active_campaign_id is None:
        _show_message(window, qt, "Import Failed", "Open or create a campaign first.", error=True)
        return
    url = ask_character_url(qt, window)
    if not url:
        _set_status(window, "Character URL import canceled.")
        return
    _run_import_result(
        window,
        qt,
        app,
        state,
        lambda: app.character_imports.import_url_to_campaign(url, state.active_campaign_id or ""),
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
    state.party_initiative.pop(result.character.character_id, None)
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
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Opened {campaign.name}.")


def _close_campaign(window, qt, app: DnDCombatEngineApp, state: GuiCampaignState) -> None:
    state.active_campaign_id = None
    state.selected_character_id = None
    state.party_initiative.clear()
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
    state.party_initiative.clear()
    _refresh_campaign_docks(window, qt, app, state)
    _set_status(window, f"Created {campaign.name}.")


def _refresh_campaign_docks(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
) -> None:
    docks = getattr(window, "_dnd_docks", {})
    _replace_dock_widget(docks, "Campaign", _campaign_widget(app, qt, state))
    _replace_dock_widget(docks, "Party", _party_widget(window, app, qt, state))
    _replace_dock_widget(docks, "Campaign Editor", _campaign_editor_widget(app, qt, state))
    _replace_dock_widget(docks, "Character Sheet", _character_widget(app, qt, state))


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
        message = _activate_action_button(app, state, button)
        _refresh_campaign_docks(window, qt, app, state)
    _append_workspace(window, message)
    _set_status(window, message)
    return message


def _activate_action_button(
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    button: ActionBarButton | None,
) -> str:
    if button is None:
        return "Action slot is empty."
    if state.selected_character_id is None:
        return f"Select a character before using {button.name}."
    try:
        character = app.characters.load(state.selected_character_id)
    except KeyError:
        return f"Selected character {state.selected_character_id} could not be loaded."
    if button.kind == ActionBarActionKind.SPELL:
        return _activate_spell_button(app, character, button)
    return _activate_ability_button(app, character, button)


def _activate_spell_button(
    app: DnDCombatEngineApp,
    character: Character,
    button: ActionBarButton,
) -> str:
    try:
        spell = app.compendium.load_spell(button.action_id)
    except KeyError:
        return f"{button.name} is not in the spell compendium."
    slot_message = "No spell slot used."
    if spell.level > 0:
        slot_level = max(spell.level, button.rank)
        resource = character.resources.get(f"spell_slot_{slot_level}")
        if resource is None:
            return f"{character.name} cannot cast {spell.name}: no level {slot_level} slots."
        if not resource.expend(1):
            return (
                f"{character.name} cannot cast {spell.name}: "
                f"no level {slot_level} slots remaining."
            )
        app.characters.save(character)
        slot_message = (
            f"Used level {slot_level} spell slot; "
            f"{resource.current}/{resource.maximum} remain."
        )
    damage_message = _roll_damage_profile(app, spell.damage)
    return f"{character.name} casts {spell.name}. {damage_message} {slot_message}"


def _activate_ability_button(
    app: DnDCombatEngineApp,
    character: Character,
    button: ActionBarButton,
) -> str:
    weapon = character.weapons[0] if character.weapons else None
    if weapon is None:
        return f"{character.name} uses {button.name}. No attack damage dice configured."
    damage_message = _roll_damage_profile(app, weapon.damage)
    return (
        f"{character.name} uses {button.name} with {weapon.name} "
        f"rank {button.rank}. {damage_message}"
    )


def _roll_damage_profile(app: DnDCombatEngineApp, damage: DamageProfile | None) -> str:
    if damage is None:
        return "No damage dice configured."
    parts = []
    total = 0
    for component in damage.components:
        result = app.dice.roll(component.dice)
        total += result.total
        parts.append(
            f"{result.notation} {component.damage_type.value}: "
            f"{result.total} rolls={result.rolls}"
        )
    return f"Damage {total} ({'; '.join(parts)})."


def _append_workspace(window, message: str) -> None:
    workspace = getattr(window, "_dnd_central", None)
    if workspace is None:
        return
    if hasattr(workspace, "append"):
        workspace.append(message)
        return
    if hasattr(workspace, "setText"):
        workspace.setText(message)


def _replace_dock_widget(docks: dict[str, object], title: str, widget) -> None:
    dock = docks.get(title)
    if dock is not None and hasattr(dock, "setWidget"):
        dock.setWidget(widget)


def _campaign_widget(app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    if state.active_campaign_id is None:
        return _label(qt, "No campaign open")
    return CampaignWidget.create(app, qt, state.active_campaign_id)


def _party_widget(window, app: DnDCombatEngineApp, qt, state: GuiCampaignState):
    if state.active_campaign_id is None:
        return _label(qt, "No campaign open")
    return PartyFramesWidget.create(
        app,
        qt,
        state.active_campaign_id,
        initiative_results=state.party_initiative,
        on_upload_sheet=lambda character_id: _replace_party_member_sheet(
            window,
            qt,
            app,
            state,
            character_id,
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


def _replace_party_member_sheet(
    window,
    qt,
    app: DnDCombatEngineApp,
    state: GuiCampaignState,
    character_id: str,
) -> None:
    path = choose_character_pdf(qt, window)
    if not path:
        _set_status(window, "Character PDF import canceled.")
        return
    try:
        draft = app.character_imports.preview_pdf(path)
        app.characters.save(draft.to_character(character_id))
    except ValueError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    except KeyError as exc:
        _show_message(window, qt, "Import Failed", str(exc), error=True)
        return
    state.selected_character_id = character_id
    _refresh_campaign_docks(window, qt, app, state)
    _show_message(window, qt, "Character Sheet Updated", f"Updated {draft.name}.")


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

