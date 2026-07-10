"""PySide6 widgets for the desktop GUI."""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.gui.editors import (
    add_character_to_encounter,
    add_encounter_to_campaign,
    add_monster_to_encounter,
    advance_encounter_round,
    complete_encounter,
    remove_character_from_campaign,
    remove_encounter_from_campaign,
    remove_participant_from_encounter,
    start_encounter,
)
from dnd_combat_engine.gui.panels import (
    attack_summary_text,
    campaign_reference_rows,
    campaign_rows,
    character_sheet_rows,
    encounter_participant_rows,
    encounter_rows,
    initiative_rows,
)
from dnd_combat_engine.models import CombatLog
from dnd_combat_engine.models.action_bar import ActionBar, ActionBarActionKind, ActionBarButton
from dnd_combat_engine.models.currency import CurrencyPurse
from dnd_combat_engine.models.effects import TargetKind, TargetReference
from dnd_combat_engine.models.encounters import ParticipantKind
from dnd_combat_engine.models.inventory import InventoryItem, ItemCategory
from dnd_combat_engine.models.spell_slots import (
    ensure_spell_slot_resources,
    ensure_spell_slot_resources_for_level,
)

ACTION_BAR_HOTKEYS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=")
PARTY_FRAME_FEATURES = (
    "Bless",
    "Divine Smite",
    "Great Weapon Master",
    "Hex",
    "Hunter's Mark",
    "Rage",
    "Sharpshooter",
    "Sneak Attack",
)
ACTIONABLE_ABILITY_FEATURES = (
    "Basic Attack",
    "Attack",
    "Channel Divinity: Preserve Life",
    "Channel Divinity: Turn Undead",
    "Divine Smite",
    "Great Weapon Master",
    "Rage",
    "Sharpshooter",
    "Sneak Attack",
)
CONTAINER_ITEM_IDS = {"bag_of_holding", "backpack", "pouch"}


class DiceTrayWidget:
    """Factory for the dice tray widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt):
        """Create a dice tray widget."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        input_box = qt.QtWidgets.QLineEdit("1d20")
        button = qt.QtWidgets.QPushButton("Roll")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)

        def roll() -> None:
            result = app.dice.roll(input_box.text())
            output.append(f"{result.notation}: {result.total} {result.rolls}")

        button.clicked.connect(roll)
        layout.addWidget(input_box)
        layout.addWidget(button)
        layout.addWidget(output)
        return widget


class CombatLogWidget:
    """Factory for the combat log widget."""

    @staticmethod
    def create(qt, log: CombatLog | None = None):
        """Create a combat log widget."""
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        for entry in (log or CombatLog()).entries:
            output.append(entry.message)
        return output


class CampaignActivityWidget:
    """Factory for persisted campaign activity rows."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, campaign_id: str | None = None):
        """Create a compact persisted campaign activity widget."""
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        if campaign_id is None:
            output.append("No campaign open")
            return output
        try:
            campaign = app.campaigns.load(campaign_id)
        except KeyError:
            output.append("Campaign activity unavailable")
            return output
        if not campaign.activity_log:
            output.append("No campaign activity yet.")
            return output
        for entry in campaign.activity_log[-12:]:
            output.append(f"[{entry.category}] {entry.message}")
        return output


class CharacterSheetWidget:
    """Factory for the character sheet widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, character_id: str = "vale"):
        """Create a compact character sheet widget."""
        character = app.characters.load(character_id)
        rows = character_sheet_rows(character)
        table = qt.QtWidgets.QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Field", "Value"])
        for row, (field, value) in enumerate(rows):
            table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(field))
            table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(value))
        return table


class CampaignWidget:
    """Factory for the campaign workspace widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, campaign_id: str = "starter_campaign"):
        """Create a compact campaign workspace widget."""
        campaign = app.campaigns.load(campaign_id)
        rows = campaign_rows(campaign)
        table = qt.QtWidgets.QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Field", "Value"])
        for row, (field, value) in enumerate(rows):
            table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(field))
            table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(value))
        return table


class PartyFramesWidget:
    """Factory for framed party member summaries."""

    @staticmethod
    def create(
        app: DnDCombatEngineApp,
        qt,
        campaign_id: str = "starter_campaign",
        initiative_results: dict[str, int] | None = None,
        beacon_of_hope_targets: tuple[str, ...] = (),
        bless_targets: tuple[str, ...] = (),
        on_upload_sheet=None,
        on_remove_member=None,
        on_set_initiative=None,
    ):
        """Create party frames for every character in a campaign."""
        campaign = app.campaigns.load(campaign_id)
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        if not campaign.character_ids:
            layout.addWidget(qt.QtWidgets.QLabel("No party members"))
            return widget
        for character_id in campaign.character_ids:
            layout.addWidget(
                _party_member_frame(
                    app,
                    qt,
                    character_id,
                    initiative_results or {},
                    beacon_of_hope_targets,
                    bless_targets,
                    on_upload_sheet,
                    on_remove_member,
                    on_set_initiative,
                )
            )
        if hasattr(layout, "addStretch"):
            layout.addStretch(1)
        return widget


class TargetPanelWidget:
    """Factory for active target selection controls."""

    @staticmethod
    def create(
        app: DnDCombatEngineApp,
        qt,
        campaign_id: str | None,
        active_target: TargetReference | None = None,
        on_select=None,
    ):
        """Create a target selector for party and encounter participants."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        active_text = "No target selected"
        if active_target is not None:
            active_text = f"Target: {active_target.name} ({active_target.kind.value})"
        layout.addWidget(qt.QtWidgets.QLabel(active_text))
        targets = _target_panel_references(app, campaign_id)
        if not targets:
            layout.addWidget(qt.QtWidgets.QLabel("No targets available"))
            return widget
        for target in targets:
            button = qt.QtWidgets.QPushButton(_target_button_text(app, target))
            if hasattr(button, "setToolTip"):
                button.setToolTip(f"Set active target to {target.name}")
            if (
                active_target is not None
                and target.target_id == active_target.target_id
                and hasattr(button, "setStyleSheet")
            ):
                button.setStyleSheet("border:2px solid #4f8cff; text-align:left;")
            button.clicked.connect(
                lambda checked=False, item=target: on_select(item)
                if on_select is not None
                else None
            )
            layout.addWidget(button)
        if hasattr(layout, "addStretch"):
            layout.addStretch(1)
        return widget


def _target_panel_references(
    app: DnDCombatEngineApp,
    campaign_id: str | None,
) -> tuple[TargetReference, ...]:
    if campaign_id is None:
        return ()
    try:
        campaign = app.campaigns.load(campaign_id)
    except KeyError:
        return ()
    targets: list[TargetReference] = []
    for character_id in campaign.character_ids:
        try:
            character = app.characters.load(character_id)
        except KeyError:
            continue
        targets.append(
            TargetReference(
                target_id=character.character_id,
                name=character.name,
                kind=TargetKind.CHARACTER,
                source_id=character.character_id,
            )
        )
    for encounter_id in campaign.encounter_ids:
        try:
            encounter = app.encounters.load(encounter_id)
        except KeyError:
            continue
        for participant in encounter.participants:
            if participant.kind is ParticipantKind.MONSTER:
                targets.append(
                    TargetReference(
                        target_id=participant.participant_id,
                        name=participant.name,
                        kind=TargetKind.MONSTER,
                        source_id=participant.source_id,
                    )
                )
    return tuple(targets)


def _target_button_text(app: DnDCombatEngineApp, target: TargetReference) -> str:
    if target.kind is TargetKind.CHARACTER:
        try:
            character = app.characters.load(target.source_id)
        except KeyError:
            return f"{target.name}\nMissing character"
        return (
            f"{character.name}\n"
            f"HP {character.hit_points.current}/{character.hit_points.maximum} "
            f"THP {character.hit_points.temporary}"
        )
    if target.kind is TargetKind.MONSTER:
        try:
            monster = app.compendium.load_monster(target.source_id)
        except KeyError:
            return f"{target.name}\nMissing monster"
        current_hp = _monster_target_current_hp(app, target, monster.hit_points.maximum)
        return f"{target.name}\nHP {current_hp}/{monster.hit_points.maximum}"
    return target.name


def _monster_target_current_hp(
    app: DnDCombatEngineApp,
    target: TargetReference,
    default_hp: int,
) -> int:
    try:
        encounter_ids = app.encounters.persistence_service.list_encounter_ids()
    except AttributeError:
        return default_hp
    for encounter_id in encounter_ids:
        try:
            encounter = app.encounters.load(encounter_id)
        except KeyError:
            continue
        for participant in encounter.participants:
            if participant.participant_id == target.target_id:
                return participant.current_hit_points or default_hp * participant.quantity
    return default_hp


class CampaignEditorWidget:
    """Factory for campaign editing controls."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, campaign_id: str = "starter_campaign"):
        """Create a campaign editor widget."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        campaign = app.campaigns.load(campaign_id)
        character_input = _campaign_character_selector(qt, campaign.character_ids)
        encounter_input = qt.QtWidgets.QLineEdit("roadside_ambush")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)

        _add_rows(output, campaign_reference_rows(campaign))

        def run(action) -> None:
            try:
                message = action()
            except ValueError as exc:
                message = str(exc)
            except KeyError as exc:
                message = str(exc)
            output.append(message)

        remove_character = qt.QtWidgets.QPushButton("Remove Character")
        remove_character.clicked.connect(
            lambda: run(
                lambda: remove_character_from_campaign(
                    app,
                    campaign_id,
                    _selector_text(character_input),
                )
            )
        )
        add_encounter = qt.QtWidgets.QPushButton("Add Encounter")
        add_encounter.clicked.connect(
            lambda: run(lambda: add_encounter_to_campaign(app, campaign_id, encounter_input.text()))
        )
        remove_encounter = qt.QtWidgets.QPushButton("Remove Encounter")
        remove_encounter.clicked.connect(
            lambda: run(
                lambda: remove_encounter_from_campaign(app, campaign_id, encounter_input.text())
            )
        )

        layout.addWidget(character_input)
        layout.addWidget(remove_character)
        layout.addWidget(encounter_input)
        layout.addWidget(add_encounter)
        layout.addWidget(remove_encounter)
        layout.addWidget(output)
        return widget


def _campaign_character_selector(qt, character_ids: tuple[str, ...]):
    combo_class = getattr(qt.QtWidgets, "QComboBox", None)
    if combo_class is None:
        return qt.QtWidgets.QLineEdit(character_ids[0] if character_ids else "")
    combo = combo_class()
    for character_id in character_ids:
        combo.addItem(character_id)
    return combo


def _selector_text(widget) -> str:
    if hasattr(widget, "currentText"):
        return str(widget.currentText()).strip()
    if hasattr(widget, "text"):
        return str(widget.text()).strip()
    return ""


class ActionBarWidget:
    """Factory for the bottom quick action bar."""

    @staticmethod
    def create(
        qt,
        session: ActionBarSession,
        on_activate=None,
        app: DnDCombatEngineApp | None = None,
    ):
        """Create a centered action bar widget."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QHBoxLayout(widget)
        if hasattr(layout, "setAlignment"):
            layout.setAlignment(qt.QtCore.Qt.AlignmentFlag.AlignCenter)
        buttons = []
        button_class = _action_bar_button_class(qt, session, on_activate)
        for slot in range(1, 13):
            button = button_class("", slot)
            if hasattr(button, "setFixedSize"):
                button.setFixedSize(92, 64)
            if hasattr(button, "setStyleSheet"):
                button.setStyleSheet("text-align: left top; padding: 4px;")
            hotkey = ACTION_BAR_HOTKEYS[slot - 1]
            if hasattr(button, "setShortcut"):
                button.setShortcut(hotkey)
            button.clicked.connect(
                lambda checked=False, item_slot=slot: _activate_action_button(
                    session,
                    on_activate,
                    item_slot,
                    False,
                )
            )
            buttons.append(button)
            layout.addWidget(button)

        def refresh(bar: ActionBar) -> None:
            for slot, button in enumerate(buttons, start=1):
                action = bar.button_at(slot)
                hotkey = ACTION_BAR_HOTKEYS[slot - 1]
                text = _action_button_text(hotkey, action)
                if hasattr(button, "setText"):
                    button.setText(text)
                if hasattr(button, "setEnabled"):
                    button.setEnabled(action is not None)
                if hasattr(button, "setToolTip"):
                    button.setToolTip(_action_bar_tooltip(hotkey, slot, action, app))

        session.subscribe(refresh)
        return widget


class SpellSlotTrackerWidget:
    """Factory for compact spell slot tracking next to the action bar."""

    @staticmethod
    def create(
        app: DnDCombatEngineApp,
        qt,
        character_id: str | None = None,
        action_bar=None,
    ):
        """Create a compact spell slot tracker for a character."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        layout.addWidget(qt.QtWidgets.QLabel("Spell Slots"))
        if character_id is None:
            layout.addWidget(qt.QtWidgets.QLabel("No leader"))
            return widget
        try:
            character = app.characters.load(character_id)
        except KeyError:
            layout.addWidget(qt.QtWidgets.QLabel("Missing leader"))
            return widget
        changed = ensure_spell_slot_resources(character)
        if action_bar is not None:
            changed = _ensure_spell_slots_for_action_bar(character, action_bar) or changed
        if changed and hasattr(app.characters, "save"):
            app.characters.save(character)
        slot_rows = _spell_slot_rows(character.resources)
        if not slot_rows:
            layout.addWidget(qt.QtWidgets.QLabel("None"))
            return widget
        for level, current, maximum in slot_rows:
            row = qt.QtWidgets.QWidget()
            row_layout = qt.QtWidgets.QHBoxLayout(row)
            row_layout.addWidget(qt.QtWidgets.QLabel(f"L{level}"))
            for index in range(maximum):
                checkbox_class = getattr(qt.QtWidgets, "QCheckBox", None)
                slot = (
                    checkbox_class()
                    if checkbox_class is not None
                    else qt.QtWidgets.QLabel("x" if index < current else "-")
                )
                if hasattr(slot, "setChecked"):
                    slot.setChecked(index < current)
                if hasattr(slot, "setEnabled"):
                    slot.setEnabled(False)
                if hasattr(slot, "setToolTip"):
                    status = "available" if index < current else "spent"
                    slot.setToolTip(f"Level {level} spell slot {index + 1}: {status}")
                row_layout.addWidget(slot)
            layout.addWidget(row)
        return widget


class SavingThrowWidget:
    """Factory for quick saving throw buttons."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, character_id: str | None, on_roll=None):
        """Create a two-column saving throw button cluster."""
        widget = qt.QtWidgets.QWidget()
        layout_class = getattr(
            qt.QtWidgets,
            "QGridLayout",
            getattr(qt.QtWidgets, "QVBoxLayout", getattr(qt.QtWidgets, "QHBoxLayout", None)),
        )
        if layout_class is None or not hasattr(qt.QtWidgets, "QPushButton"):
            return None
        layout = layout_class(widget)
        if character_id is None:
            layout.addWidget(qt.QtWidgets.QLabel("Saves"))
            return widget
        try:
            character = app.characters.load(character_id)
        except KeyError:
            layout.addWidget(qt.QtWidgets.QLabel("Saves"))
            return widget
        saves = (
            ("strength", "STR", 0, 0),
            ("intelligence", "INT", 0, 1),
            ("dexterity", "DEX", 1, 0),
            ("wisdom", "WIS", 1, 1),
            ("constitution", "CON", 2, 0),
            ("charisma", "CHA", 2, 1),
        )
        proficiencies = {name.lower() for name in character.saving_throw_proficiencies}
        for ability, label, row, column in saves:
            button = qt.QtWidgets.QPushButton(label)
            proficient = ability in proficiencies
            if proficient and hasattr(button, "setStyleSheet"):
                button.setStyleSheet("border-left: 4px solid #4f8cff;")
            if hasattr(button, "setToolTip"):
                modifier = character.abilities.modifier(ability)  # type: ignore[arg-type]
                bonus = _proficiency_bonus(character.level) if proficient else 0
                button.setToolTip(
                    f"{ability.title()} save: d20 {modifier:+d}"
                    f"{' + proficiency ' + str(bonus) if proficient else ''}"
                )
            button.clicked.connect(
                lambda checked=False, save=ability: on_roll(save)
                if on_roll is not None
                else None
            )
            try:
                layout.addWidget(button, row, column)
            except TypeError:
                layout.addWidget(button)
        return widget


class SpellbookWidget:
    """Factory for the spellbook source window."""

    @staticmethod
    def create(
        app: DnDCombatEngineApp,
        qt,
        session: ActionBarSession,
        character_id: str | None = None,
    ):
        """Create a spellbook widget that can place spells on the action bar."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        layout.addWidget(qt.QtWidgets.QLabel(_spellbook_title(app, character_id)))
        tabs = _spellbook_tabs(qt)
        layout.addWidget(tabs)
        attacks_tab = _spellbook_tab(qt)
        spells_tab = _spellbook_tab(qt)
        cantrips_tab = _spellbook_tab(qt)
        abilities_tab = _spellbook_tab(qt)
        channel_tab = _spellbook_tab(qt)
        _add_spellbook_tab(tabs, spells_tab, "Spells")
        _add_spellbook_tab(tabs, abilities_tab, "Abilities")
        _add_spellbook_tab(tabs, cantrips_tab, "Cantrips")
        _add_spellbook_tab(tabs, attacks_tab, "Attacks")
        _add_spellbook_tab(tabs, channel_tab, "Channel Divinity")
        for attack_name in _attack_names_for_character(app, character_id):
            button = qt.QtWidgets.QPushButton(f"{attack_name} (Attack)")
            if hasattr(button, "setToolTip"):
                button.setToolTip(f"Place {attack_name} on the action bar.")
            button.clicked.connect(
                lambda checked=False, name=attack_name: output.append(
                    session.place_next(
                        ActionBarButton(
                            slot=1,
                            kind=ActionBarActionKind.ABILITY,
                            action_id=_action_id(name),
                            name=name,
                            rank=1,
                            uses_highest_rank=True,
                        )
                    )
                )
            )
            _spellbook_tab_add_widget(attacks_tab, button)
        for spell_id in _spell_ids_for_character(app, character_id):
            spell = app.compendium.load_spell(spell_id)
            rank_options = _spell_rank_options(app, character_id, spell)
            highest_rank = max(rank_options)
            for rank in rank_options:
                button = qt.QtWidgets.QPushButton(
                    _spell_rank_button_text(spell.name, rank, spell.level)
                )
                if hasattr(button, "setToolTip"):
                    button.setToolTip(_spell_tooltip(spell, rank))
                button.clicked.connect(
                    lambda checked=False,
                    item=spell,
                    item_rank=rank,
                    item_highest=highest_rank: output.append(
                        session.place_next(
                            ActionBarButton(
                                slot=1,
                                kind=ActionBarActionKind.SPELL,
                                action_id=item.spell_id,
                                name=item.name,
                                rank=item_rank,
                                uses_highest_rank=item_rank == item_highest,
                            )
                        )
                    )
                )
                target_tab = cantrips_tab if spell.level == 0 else spells_tab
                _spellbook_tab_add_widget(target_tab, button)
        for feature in _actionable_ability_names_for_tab(app, character_id):
            button = qt.QtWidgets.QPushButton(feature)
            if hasattr(button, "setToolTip"):
                button.setToolTip(_ability_tooltip(feature))
            button.clicked.connect(
                lambda checked=False, name=feature: output.append(
                    session.place_next(
                        ActionBarButton(
                            slot=1,
                            kind=ActionBarActionKind.ABILITY,
                            action_id=_action_id(name),
                            name=name,
                            rank=1,
                            uses_highest_rank=True,
                        )
                    )
                )
            )
            target_tab = channel_tab if _is_channel_divinity_name(feature) else abilities_tab
            _spellbook_tab_add_widget(target_tab, button)
        for tab in (spells_tab, abilities_tab, cantrips_tab, attacks_tab, channel_tab):
            _spellbook_tab_finish(qt, tab)
        layout.addWidget(output)
        return widget


def _attack_names_for_character(
    app: DnDCombatEngineApp,
    character_id: str | None,
) -> tuple[str, ...]:
    if character_id is None:
        return ()
    try:
        character = app.characters.load(character_id)
    except KeyError:
        return ()
    names = [weapon.name for weapon in character.weapons if _is_valid_attack_name(weapon.name)]
    if "Unarmed Strike" not in names:
        names.append("Unarmed Strike")
    return tuple(names)


class AbilitiesWidget:
    """Factory for the abilities source window."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, session: ActionBarSession, character_id: str = "vale"):
        """Create an abilities widget that can place character features on the action bar."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        character = app.characters.load(character_id)
        features = _actionable_ability_names(character.features)
        for feature in features:
            button = qt.QtWidgets.QPushButton(feature)
            if hasattr(button, "setToolTip"):
                button.setToolTip(_ability_tooltip(feature))
            button.clicked.connect(
                lambda checked=False, name=feature: output.append(
                    session.place_next(
                        ActionBarButton(
                            slot=1,
                            kind=ActionBarActionKind.ABILITY,
                            action_id=_action_id(name),
                            name=name,
                            rank=1,
                            uses_highest_rank=True,
                        )
                    )
                )
            )
            layout.addWidget(button)
        layout.addWidget(output)
        return widget


def _spellbook_tabs(qt):
    tab_class = getattr(qt.QtWidgets, "QTabWidget", None)
    if tab_class is None:
        return _FallbackTabs(qt)
    tabs = tab_class()
    tab_position = getattr(tab_class, "TabPosition", tab_class)
    east = getattr(tab_position, "East", None)
    if east is not None and hasattr(tabs, "setTabPosition"):
        tabs.setTabPosition(east)
    return tabs


class _FallbackTabs:
    def __init__(self, qt) -> None:
        self.widget = qt.QtWidgets.QWidget()
        self.layout = qt.QtWidgets.QVBoxLayout(self.widget)

    def addTab(self, widget, title: str) -> None:  # noqa: N802
        self.layout.addWidget(widget)


def _spellbook_tab(qt):
    widget = qt.QtWidgets.QWidget()
    layout = qt.QtWidgets.QVBoxLayout(widget)
    widget._dnd_spellbook_tab_layout = layout  # noqa: SLF001
    widget._dnd_spellbook_tab_count = 0  # noqa: SLF001
    return widget


def _add_spellbook_tab(tabs, tab, title: str) -> None:
    if hasattr(tabs, "addTab"):
        tabs.addTab(tab, title)


def _spellbook_tab_add_widget(tab, widget) -> None:
    layout = getattr(tab, "_dnd_spellbook_tab_layout", None)
    if layout is None:
        return
    layout.addWidget(widget)
    tab._dnd_spellbook_tab_count = getattr(tab, "_dnd_spellbook_tab_count", 0) + 1  # noqa: SLF001


def _spellbook_tab_finish(qt, tab) -> None:
    layout = getattr(tab, "_dnd_spellbook_tab_layout", None)
    if layout is None:
        return
    if getattr(tab, "_dnd_spellbook_tab_count", 0) == 0:
        layout.addWidget(qt.QtWidgets.QLabel("None available"))
    if hasattr(layout, "addStretch"):
        layout.addStretch(1)


def _actionable_ability_names_for_tab(
    app: DnDCombatEngineApp,
    character_id: str | None,
) -> tuple[str, ...]:
    if character_id is None:
        return ()
    try:
        character = app.characters.load(character_id)
    except KeyError:
        return ()
    return _actionable_ability_names(character.features)


def _is_channel_divinity_name(name: str) -> bool:
    return name.lower().startswith("channel divinity")


class InventoryWidget:
    """Factory for an RPG-style inventory window."""

    @staticmethod
    def create(
        app: DnDCombatEngineApp,
        qt,
        character_id: str,
        on_consume=None,
        on_sell=None,
        on_currency_change=None,
        on_add_item=None,
    ):
        """Create an icon inventory grouped by carried containers."""
        character = app.characters.load(character_id)
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        layout.addWidget(
            _inventory_header(
                qt,
                character.name,
                character.currency,
                on_currency_change,
                on_add_item,
            )
        )
        sections = _inventory_sections(character.inventory)
        for section_name, items in sections:
            section = _inventory_section(qt, section_name, items, on_consume, on_sell)
            layout.addWidget(section)
        if hasattr(layout, "addStretch"):
            layout.addStretch(1)
        return widget


def _inventory_header(
    qt,
    character_name: str,
    purse: CurrencyPurse,
    on_currency_change,
    on_add_item=None,
):
    widget = qt.QtWidgets.QWidget()
    layout = qt.QtWidgets.QHBoxLayout(widget)
    layout.addWidget(qt.QtWidgets.QLabel(f"Inventory: {character_name}"))
    if hasattr(layout, "addStretch"):
        layout.addStretch(1)
    if on_add_item is not None:
        add_item_button = qt.QtWidgets.QPushButton("Add Item")
        if hasattr(add_item_button, "setToolTip"):
            add_item_button.setToolTip("Manually add an item stack to this inventory.")
        add_item_button.clicked.connect(lambda checked=False: on_add_item())
        layout.addWidget(add_item_button)
    money_log = [f"Opening balance: {_currency_price_text(purse.total_cp)}"]
    money_log_button = qt.QtWidgets.QPushButton("Money Log")
    if hasattr(money_log_button, "setToolTip"):
        money_log_button.setToolTip("Show currency changes made while this inventory is open.")
    layout.addWidget(money_log_button)
    ledger = qt.QtWidgets.QLineEdit()
    if hasattr(ledger, "setPlaceholderText"):
        ledger.setPlaceholderText("1PP 100GP")
    layout.addWidget(ledger)
    buttons = qt.QtWidgets.QWidget()
    button_layout = qt.QtWidgets.QVBoxLayout(buttons)
    deposit = qt.QtWidgets.QPushButton("Deposit")
    withdraw = qt.QtWidgets.QPushButton("Withdraw")
    if hasattr(deposit, "setStyleSheet"):
        deposit.setStyleSheet("background:#1f7a3a; color:white;")
    if hasattr(withdraw, "setStyleSheet"):
        withdraw.setStyleSheet("background:#9f2f2f; color:white;")
    button_layout.addWidget(deposit)
    button_layout.addWidget(withdraw)
    layout.addWidget(buttons)
    boxes = _currency_boxes(qt, purse)
    layout.addWidget(_currency_box_grid(qt, boxes))
    current = {"purse": purse}

    def apply_ledger(multiplier: int) -> None:
        if on_currency_change is None:
            return
        entry_text = ledger.text()
        try:
            amount = CurrencyPurse.parse(entry_text).total_cp * multiplier
            updated = on_currency_change(amount)
        except ValueError as exc:
            if hasattr(ledger, "setText"):
                ledger.setText(str(exc))
            return
        if updated is not None:
            current["purse"] = updated
            action = "Deposit" if multiplier > 0 else "Withdraw"
            money_log.append(
                _money_log_entry(action, abs(amount), updated, raw_entry=entry_text)
            )
            _set_currency_boxes(boxes, updated)
            if hasattr(ledger, "clear"):
                ledger.clear()

    def apply_boxes() -> None:
        if on_currency_change is None:
            return
        try:
            target = CurrencyPurse(
                **{label.lower(): max(int(box.text() or "0"), 0) for label, box in boxes}
            )
            delta_cp = target.total_cp - current["purse"].total_cp
            updated = on_currency_change(delta_cp)
        except ValueError as exc:
            if hasattr(ledger, "setText"):
                ledger.setText(str(exc))
            _set_currency_boxes(boxes, current["purse"])
            return
        if updated is not None:
            current["purse"] = updated
            if delta_cp:
                money_log.append(_money_log_entry("Set Currency", delta_cp, updated))
            _set_currency_boxes(boxes, updated)

    money_log_button.clicked.connect(
        lambda checked=False: _show_money_log(qt, widget, character_name, money_log, current)
    )
    deposit.clicked.connect(lambda checked=False: apply_ledger(1))
    withdraw.clicked.connect(lambda checked=False: apply_ledger(-1))
    for _, box in boxes:
        signal = getattr(box, "editingFinished", None)
        if signal is not None and hasattr(signal, "connect"):
            signal.connect(apply_boxes)
    return widget


def _show_money_log(qt, parent, character_name: str, entries: list[str], current: dict):
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    if dialog_class is None:
        return None
    try:
        dialog = dialog_class(parent)
    except TypeError:
        dialog = dialog_class()
    if hasattr(dialog, "setWindowTitle"):
        dialog.setWindowTitle(f"{character_name} Money Log")
    if hasattr(dialog, "resize"):
        dialog.resize(360, 320)
    layout = qt.QtWidgets.QVBoxLayout(dialog)
    text = "\n".join(_money_log_lines(entries, current["purse"]))
    text_edit_class = getattr(qt.QtWidgets, "QTextEdit", None)
    if text_edit_class is not None:
        output = text_edit_class()
        if hasattr(output, "setReadOnly"):
            output.setReadOnly(True)
        _set_text_content(output, text)
    else:
        output = qt.QtWidgets.QLabel(text)
    layout.addWidget(output)
    dialogs = getattr(parent, "_dnd_money_log_dialogs", [])
    dialogs.append(dialog)
    parent._dnd_money_log_dialogs = dialogs  # noqa: SLF001
    if hasattr(dialog, "show"):
        dialog.show()
    return dialog


def _money_log_lines(entries: list[str], current_purse: CurrencyPurse) -> tuple[str, ...]:
    return (*entries, f"Current balance: {_currency_price_text(current_purse.total_cp)}")


def _money_log_entry(
    action: str,
    amount_cp: int,
    updated: CurrencyPurse,
    raw_entry: str | None = None,
) -> str:
    amount_text = _currency_delta_text(amount_cp)
    if raw_entry:
        amount_text = f"{raw_entry.strip()} ({amount_text})"
    return f"{action}: {amount_text} -> {_currency_price_text(updated.total_cp)}"


def _currency_delta_text(amount_cp: int) -> str:
    prefix = "-" if amount_cp < 0 else "+"
    return f"{prefix}{_currency_price_text(abs(amount_cp))}"


def _set_text_content(widget, text: str) -> None:
    if hasattr(widget, "setPlainText"):
        widget.setPlainText(text)
    elif hasattr(widget, "setText"):
        widget.setText(text)


def _currency_boxes(qt, purse: CurrencyPurse):
    boxes = []
    for label, value in (
        ("PP", purse.pp),
        ("GP", purse.gp),
        ("SP", purse.sp),
        ("CP", purse.cp),
    ):
        box = qt.QtWidgets.QLineEdit(str(value))
        if hasattr(box, "setFixedWidth"):
            box.setFixedWidth(48)
        boxes.append((label, box))
    return tuple(boxes)


def _currency_box_grid(qt, boxes):
    widget = qt.QtWidgets.QWidget()
    grid_class = getattr(qt.QtWidgets, "QGridLayout", qt.QtWidgets.QVBoxLayout)
    layout = grid_class(widget)
    for index, (label, box) in enumerate(boxes):
        row, column = divmod(index, 2)
        cell = qt.QtWidgets.QWidget()
        cell_layout = qt.QtWidgets.QHBoxLayout(cell)
        cell_layout.addWidget(qt.QtWidgets.QLabel(label))
        cell_layout.addWidget(box)
        try:
            layout.addWidget(cell, row, column)
        except TypeError:
            layout.addWidget(cell)
    return widget


def _set_currency_boxes(boxes, purse: CurrencyPurse) -> None:
    values = {"PP": purse.pp, "GP": purse.gp, "SP": purse.sp, "CP": purse.cp}
    for label, box in boxes:
        if hasattr(box, "setText"):
            box.setText(str(values[label]))


def _inventory_section(
    qt,
    section_name: str,
    items: tuple[InventoryItem, ...],
    on_consume,
    on_sell,
):
    group_class = getattr(qt.QtWidgets, "QGroupBox", qt.QtWidgets.QWidget)
    try:
        group = group_class(section_name)
    except TypeError:
        group = group_class()
    if hasattr(group, "setStyleSheet"):
        group.setStyleSheet("QGroupBox { margin-top: 8px; padding-top: 8px; }")
    grid_class = getattr(qt.QtWidgets, "QGridLayout", qt.QtWidgets.QVBoxLayout)
    layout = grid_class(group)
    for index, item in enumerate(items):
        button = _inventory_item_button(qt, item, on_consume, on_sell)
        row, column = divmod(index, 6)
        if hasattr(layout, "addWidget"):
            try:
                layout.addWidget(button, row, column)
            except TypeError:
                layout.addWidget(button)
    if not items:
        layout.addWidget(qt.QtWidgets.QLabel("Empty"))
    return group


def _inventory_item_button(qt, item: InventoryItem, on_consume, on_sell):
    button_class = _inventory_button_class(qt, item, on_consume, on_sell)
    button = button_class(_inventory_quantity_text(item))
    if hasattr(button, "setToolTip"):
        button.setToolTip(_inventory_item_tooltip(item))
    if hasattr(button, "setFixedSize"):
        button.setFixedSize(72, 72)
    if hasattr(button, "setStyleSheet"):
        button.setStyleSheet(
            "text-align: left bottom; padding: 3px; background:#151922; border:1px solid #303747;"
        )
    icon_path = _inventory_icon_path(item)
    if icon_path is not None:
        icon = qt.QtGui.QIcon(str(icon_path))
        if hasattr(button, "setIcon"):
            button.setIcon(icon)
        if hasattr(button, "setIconSize") and hasattr(qt.QtCore, "QSize"):
            button.setIconSize(qt.QtCore.QSize(48, 48))
    return button


def _inventory_button_class(qt, item: InventoryItem, on_consume, on_sell):
    base_class = qt.QtWidgets.QPushButton

    class ConsumableInventoryButton(base_class):
        def mousePressEvent(self, event) -> None:  # noqa: N802
            if _is_right_click(qt, event) and any((on_consume, on_sell)):
                _show_inventory_item_menu(qt, self, item, on_consume, on_sell, event)
                if hasattr(event, "accept"):
                    event.accept()
                return
            super().mousePressEvent(event)

    return ConsumableInventoryButton


def _show_inventory_item_menu(qt, button, item: InventoryItem, on_consume, on_sell, event) -> None:
    menu_class = getattr(qt.QtWidgets, "QMenu", None)
    if menu_class is None:
        _consume_inventory_button_item(button, item, on_consume)
        return
    menu = menu_class(button)
    if on_consume is not None:
        consume_action = menu.addAction("Consume")
        if item.category != ItemCategory.CONSUMABLE and hasattr(consume_action, "setEnabled"):
            consume_action.setEnabled(False)
        if hasattr(consume_action, "triggered"):
            consume_action.triggered.connect(
                lambda checked=False: _consume_inventory_button_item(button, item, on_consume)
            )
    if on_sell is not None:
        sell_action = menu.addAction(f"Sell ({_currency_price_text(_sell_price_cp(item))})")
        if hasattr(sell_action, "triggered"):
            sell_action.triggered.connect(
                lambda checked=False: _sell_inventory_button_item(button, item, on_sell)
            )
    position = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else None
    if position is None:
        position = event.globalPos() if hasattr(event, "globalPos") else None
    if position is None and hasattr(button, "mapToGlobal"):
        position = button.mapToGlobal(event.pos())
    if hasattr(menu, "exec"):
        menu.exec(position)
    elif hasattr(menu, "exec_"):
        menu.exec_(position)


def _consume_inventory_button_item(button, item: InventoryItem, on_consume) -> None:
    if on_consume is None:
        return
    remaining = on_consume(item.item_id)
    _set_inventory_button_remaining(button, remaining)


def _sell_inventory_button_item(button, item: InventoryItem, on_sell) -> None:
    if on_sell is None:
        return
    remaining = on_sell(item.item_id)
    _set_inventory_button_remaining(button, remaining)


def _set_inventory_button_remaining(button, remaining) -> None:
    if not isinstance(remaining, int):
        return
    if remaining <= 0 and hasattr(button, "setEnabled"):
        button.setEnabled(False)
    if hasattr(button, "setText"):
        button.setText(str(remaining) if remaining > 1 else "")


def _sell_price_cp(item: InventoryItem) -> int:
    price_cp = item.purchase_price_cp or _default_purchase_price_cp(item)
    return max(price_cp // 2, 0)


def _inventory_quantity_text(item: InventoryItem) -> str:
    return str(item.quantity) if item.quantity > 1 else ""


def _inventory_sections(
    inventory: tuple[InventoryItem, ...],
) -> tuple[tuple[str, tuple[InventoryItem, ...]], ...]:
    sections: list[tuple[str, list[InventoryItem]]] = [("Carried", [])]
    for item in inventory:
        if _is_container_item(item):
            sections.append((item.name, []))
            continue
        sections[-1][1].append(item)
    return tuple((name, tuple(items)) for name, items in sections)


def _is_container_item(item: InventoryItem) -> bool:
    normalized = _action_id(item.name)
    return item.item_id in CONTAINER_ITEM_IDS or normalized in CONTAINER_ITEM_IDS


def _inventory_icon_path(item: InventoryItem) -> Path | None:
    icon_root = Path(__file__).resolve().parents[1] / "data" / "item_icons"
    candidates = _inventory_icon_candidates(item)
    for candidate in candidates:
        path = icon_root / f"{candidate}.svg"
        if path.exists():
            return path
    fallback = icon_root / f"{item.category.value}.svg"
    return fallback if fallback.exists() else None


def _inventory_icon_candidates(item: InventoryItem) -> tuple[str, ...]:
    names = [item.item_id, _action_id(item.name)]
    aliases = {
        "acid": "consumable",
        "alchemists_fire": "consumable",
        "antitoxin": "potion",
        "arcane_focus": "focus",
        "arrows_20": "arrows",
        "bag_of_holding": "bag_of_holding",
        "bagpipes": "instrument",
        "ball_bearings": "adventuring_gear",
        "barrel": "container",
        "basket": "container",
        "bedroll": "adventuring_gear",
        "bell": "tool",
        "blanket": "clothing",
        "bolts_20": "arrows",
        "book": "book",
        "bottle_glass": "potion",
        "bullseye_lantern": "bullseye_lantern",
        "bullets_firearm_10": "ammunition",
        "bullets_sling_20": "ammunition",
        "burglar_s_pack": "backpack",
        "caltrops": "trap",
        "candle": "light_source",
        "case_crossbow_bolt": "container",
        "case_map_or_scroll": "scroll",
        "chest": "container",
        "climber_s_kit": "tool",
        "clothes_common": "common_clothes",
        "clothes_fine": "clothing",
        "clothes_traveler_s": "clothing",
        "component_pouch": "pouch",
        "costume": "clothing",
        "crystal": "focus",
        "dice_set": "game",
        "diplomat_s_pack": "backpack",
        "dragonchess_set": "game",
        "druidic_focus": "focus",
        "dungeoneer_s_pack": "backpack",
        "emblem_borne_on_fabric_or_a_shield": "holy_symbol",
        "entertainer_s_pack": "backpack",
        "explorer_s_pack": "backpack",
        "flask": "potion",
        "flute": "instrument",
        "forgery_kit": "tool",
        "grappling_hook": "adventuring_gear",
        "healers_kit": "healers_kit",
        "herbalism_kit": "tool",
        "holy_symbol": "holy_symbol",
        "holy_water": "potion",
        "horn": "instrument",
        "hunting_trap": "trap",
        "ink": "adventuring_gear",
        "ink_pen": "tool",
        "lantern_bullseye": "bullseye_lantern",
        "lantern_hooded": "light_source",
        "lock": "lock",
        "lute": "instrument",
        "lyre": "instrument",
        "manacles": "lock",
        "masons_tools": "mason_tools",
        "needles_50": "ammunition",
        "oil": "potion",
        "orb": "focus",
        "pan_flute": "instrument",
        "playing_card_set": "game",
        "piton": "pitons",
        "poison_basic": "potion",
        "plate": "plate_armour",
        "potion_of_healing": "potion",
        "potion_of_healing_greater": "potion_of_greater_healing",
        "priest_s_pack": "backpack",
        "ram_portable": "adventuring_gear",
        "rope": "hempen_rope",
        "rations_1_day": "rations_1_day",
        "rations": "rations_1_day",
        "reliquary_held": "holy_symbol",
        "robe": "clothing",
        "rod": "focus",
        "scholar_s_pack": "backpack",
        "scroll": "scroll",
        "shield": "shield_round",
        "spell_scroll_cantrip": "scroll",
        "spell_scroll_level_1": "scroll",
        "sprig_of_mistletoe": "focus",
        "staff_also_a_quarterstaff": "focus",
        "tent": "adventuring_gear",
        "three_dragon_ante_set": "game",
        "vial": "potion",
        "viol": "instrument",
        "wand": "focus",
        "wooden_staff_also_a_quarterstaff": "focus",
        "yew_wand": "focus",
    }
    if item.item_id in aliases:
        names.insert(0, aliases[item.item_id])
    names.extend(_inventory_tag_icon_candidates(item))
    return tuple(dict.fromkeys(names))


def _inventory_tag_icon_candidates(item: InventoryItem) -> tuple[str, ...]:
    tag_icons = {
        "ammunition": "ammunition",
        "arcane focus": "focus",
        "container": "container",
        "druidic focus": "focus",
        "gaming set": "game",
        "healing": "potion",
        "holy symbol": "holy_symbol",
        "large vehicle": "vehicle",
        "mount": "mount",
        "musical instrument": "instrument",
        "potion": "potion",
        "scroll": "scroll",
        "service": "treasure",
        "vehicle": "vehicle",
    }
    return tuple(tag_icons[tag] for tag in item.tags if tag in tag_icons)


def _is_right_click(qt, event) -> bool:
    button = event.button() if hasattr(event, "button") else None
    mouse_button = getattr(getattr(qt.QtCore.Qt, "MouseButton", None), "RightButton", None)
    if mouse_button is None:
        mouse_button = getattr(qt.QtCore.Qt, "RightButton", None)
    return mouse_button is not None and button == mouse_button


class EncounterTrackerWidget:
    """Factory for the encounter tracker widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, encounter_id: str = "roadside_ambush"):
        """Create a compact encounter tracker widget."""
        encounter = app.encounters.load(encounter_id)
        rows = encounter_rows(encounter)
        table = qt.QtWidgets.QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Field", "Value"])
        for row, (field, value) in enumerate(rows):
            table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(field))
            table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(value))
        return table


class EncounterEditorWidget:
    """Factory for encounter editing controls."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, encounter_id: str = "roadside_ambush"):
        """Create an encounter editor widget."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        character_input = qt.QtWidgets.QLineEdit("vale")
        monster_input = qt.QtWidgets.QLineEdit("goblin")
        quantity_input = qt.QtWidgets.QLineEdit("1")
        participant_input = qt.QtWidgets.QLineEdit("goblin")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)

        _add_participants(output, encounter_participant_rows(app.encounters.load(encounter_id)))

        def run(action) -> None:
            try:
                message = action()
            except ValueError as exc:
                message = str(exc)
            except KeyError as exc:
                message = str(exc)
            output.append(message)

        add_character = qt.QtWidgets.QPushButton("Add Character")
        add_character.clicked.connect(
            lambda: run(
                lambda: add_character_to_encounter(app, encounter_id, character_input.text())
            )
        )
        add_monster = qt.QtWidgets.QPushButton("Add Monster")
        add_monster.clicked.connect(
            lambda: run(
                lambda: add_monster_to_encounter(
                    app,
                    encounter_id,
                    monster_input.text(),
                    int(quantity_input.text()),
                )
            )
        )
        remove_participant = qt.QtWidgets.QPushButton("Remove Participant")
        remove_participant.clicked.connect(
            lambda: run(
                lambda: remove_participant_from_encounter(
                    app,
                    encounter_id,
                    participant_input.text(),
                )
            )
        )
        start_button = qt.QtWidgets.QPushButton("Start")
        start_button.clicked.connect(lambda: run(lambda: start_encounter(app, encounter_id)))
        advance_button = qt.QtWidgets.QPushButton("Advance Round")
        advance_button.clicked.connect(
            lambda: run(lambda: advance_encounter_round(app, encounter_id))
        )
        complete_button = qt.QtWidgets.QPushButton("Complete")
        complete_button.clicked.connect(lambda: run(lambda: complete_encounter(app, encounter_id)))

        layout.addWidget(character_input)
        layout.addWidget(add_character)
        layout.addWidget(monster_input)
        layout.addWidget(quantity_input)
        layout.addWidget(add_monster)
        layout.addWidget(participant_input)
        layout.addWidget(remove_participant)
        layout.addWidget(start_button)
        layout.addWidget(advance_button)
        layout.addWidget(complete_button)
        layout.addWidget(output)
        return widget


class InitiativeWidget:
    """Factory for the initiative widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, character_id: str = "vale"):
        """Create a compact initiative widget."""
        character = app.characters.load(character_id)
        encounter = app.encounters.add_character(app.encounters.load("roadside_ambush"), character)
        _, tracker = app.encounters.start_and_roll_initiative(encounter, (character,))
        rows = initiative_rows(tracker)
        table = qt.QtWidgets.QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Position", "Combatant"])
        for row, (field, value) in enumerate(rows):
            table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(field))
            table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(value))
        return table


class AttackPanelWidget:
    """Factory for the quick attack widget."""

    @staticmethod
    def create(
        app: DnDCombatEngineApp,
        qt,
        character_id: str | None = None,
        campaign_id: str = "starter_campaign",
    ):
        """Create a quick attack widget backed by controllers."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        button = qt.QtWidgets.QPushButton("Quick Attack")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)

        def attack() -> None:
            output.append(_quick_attack_message(app, character_id, campaign_id))

        button.clicked.connect(attack)
        layout.addWidget(button)
        layout.addWidget(output)
        return widget


def _quick_attack_message(
    app: DnDCombatEngineApp,
    character_id: str | None = None,
    campaign_id: str = "starter_campaign",
) -> str:
    """Resolve a quick attack and return a panel-safe message."""
    try:
        attacker_id = character_id or _first_campaign_character_id(app, campaign_id)
        attacker = app.characters.load(attacker_id)
        if not attacker.weapons:
            return f"{attacker.name} has no weapon configured for Quick Attack."
        monster = app.compendium.load_monster("goblin")
        target = attacker.__class__(
            character_id=monster.monster_id,
            name=monster.name,
            hit_points=monster.hit_points,
            abilities=monster.abilities,
        )
        result = app.combat.attack_with_weapon(
            attacker=attacker,
            target=target,
            weapon=attacker.weapons[0],
            target_armor_class=monster.armor_class,
            attack_bonus=5,
            active_features=_quick_attack_features(attacker.features),
        )
    except (KeyError, ValueError, IndexError) as exc:
        return f"Quick Attack failed: {exc}"
    return attack_summary_text(result)


def _first_campaign_character_id(app: DnDCombatEngineApp, campaign_id: str) -> str:
    try:
        campaign = app.campaigns.load(campaign_id)
    except KeyError:
        return "vale"
    return campaign.character_ids[0] if campaign.character_ids else "vale"


def _quick_attack_features(features: tuple[str, ...]) -> tuple[str, ...]:
    feature_names = {feature.lower() for feature in _party_frame_feature_candidates(features)}
    active = [
        feature
        for feature in ("Sneak Attack", "Bless", "Rage", "Hex")
        if feature.lower() in feature_names
    ]
    return tuple(active)


def _add_rows(output, rows: list[tuple[str, str]]) -> None:
    for field, value in rows:
        output.append(f"{field}: {value}")


def _add_participants(output, rows: list[tuple[str, str, str, str]]) -> None:
    for participant_id, name, kind, quantity in rows:
        output.append(f"{participant_id}: {name} ({kind}) x{quantity}")


def _spell_slot_rows(resources) -> tuple[tuple[int, int, int], ...]:
    rows = []
    for name, resource in resources.items():
        match = re.fullmatch(r"spell_slot_(\d+)", name)
        if match:
            rows.append((int(match.group(1)), resource.current, resource.maximum))
    return tuple(sorted(rows))


def _ensure_spell_slots_for_action_bar(character, action_bar) -> bool:
    changed = False
    for button in getattr(action_bar, "buttons", ()):
        if button.kind != ActionBarActionKind.SPELL:
            continue
        changed = ensure_spell_slot_resources_for_level(character, button.rank) or changed
    return changed


def _action_button_text(hotkey: str, action: ActionBarButton | None) -> str:
    """Return wrapped action bar text with the shortcut on the first line."""
    if action is None:
        return f"{hotkey}\nEmpty"
    rank = f" R{action.rank}" if action.rank > 1 else ""
    return f"{hotkey}\n{_wrap_action_label(f'{action.name}{rank}')}"


def _action_bar_tooltip(
    hotkey: str,
    slot: int,
    action: ActionBarButton | None,
    app: DnDCombatEngineApp | None = None,
) -> str:
    """Return a concise tooltip for an action bar slot."""
    if action is None:
        return f"Slot {slot} ({hotkey}) is empty."
    if action.kind == ActionBarActionKind.SPELL and app is not None:
        spell_tooltip = _action_bar_spell_tooltip(app, action)
        if spell_tooltip:
            return "\n".join(
                (
                    spell_tooltip,
                    f"Shortcut: {hotkey}",
                    "Click to cast; Shift+click rolls 1d20.",
                    "Shift+right-click to remove.",
                )
            )
    lines = [
        f"{action.name} rank {action.rank}",
        f"Type: {action.kind.value.title()}",
        f"Shortcut: {hotkey}",
    ]
    if action.kind == ActionBarActionKind.SPELL:
        lines.append("Click to cast; Shift+click rolls 1d20.")
    else:
        lines.append("Click to use; Shift+click rolls 1d20.")
    lines.append("Shift+right-click to remove.")
    return "\n".join(lines)


def _action_bar_spell_tooltip(app: DnDCombatEngineApp, action: ActionBarButton) -> str:
    """Return rich spell metadata for a spell placed on the action bar."""
    try:
        spell = app.compendium.load_spell(action.action_id)
    except (AttributeError, KeyError):
        return ""
    return _spell_tooltip(spell, action.rank)


def _wrap_action_label(label: str, width: int = 10, max_lines: int = 3) -> str:
    lines: list[str] = []
    for raw_line in label.splitlines():
        lines.extend(textwrap.wrap(raw_line, width=width, break_long_words=True) or [""])
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _truncate_wrapped_line(lines[-1], width)
    return "\n".join(lines)


def _truncate_wrapped_line(line: str, width: int) -> str:
    if width <= 3:
        return "." * width
    return f"{line[: width - 3]}..."


def _spellbook_title(app: DnDCombatEngineApp, character_id: str | None) -> str:
    if character_id is None:
        return "Spellbook"
    try:
        character = app.characters.load(character_id)
    except KeyError:
        return "Spellbook"
    return f"Spellbook: {character.name}"


def _spell_tooltip(spell, rank: int) -> str:
    """Return a spellbook tooltip from spell metadata."""
    level_text = "Cantrip" if spell.level == 0 else f"Level {spell.level}"
    cast_level_text = "Cantrip" if spell.level == 0 else f"Cast using level {rank} slot"
    lines = [
        spell.name,
        f"{level_text} {spell.school.value.title()}",
        cast_level_text,
        f"Casting Time: {spell.casting_time}",
        f"Range: {spell.range_text}",
        f"Duration: {spell.duration}",
    ]
    if spell.components:
        lines.append(f"Components: {', '.join(spell.components)}")
    if spell.concentration:
        lines.append("Requires concentration.")
    if spell.saving_throw:
        lines.append(f"Save: {spell.saving_throw}")
    if spell.damage is not None:
        lines.append(f"Damage: {_damage_profile_text(spell.damage)}")
    if spell.description:
        lines.append(_wrap_tooltip_text(spell.description))
    return "\n".join(lines)


def _spell_ids_for_character(
    app: DnDCombatEngineApp,
    character_id: str | None,
) -> tuple[str, ...]:
    spell_ids = tuple(app.compendium.persistence_service.list_spell_ids())
    if character_id is None:
        return spell_ids
    try:
        character = app.characters.load(character_id)
    except KeyError:
        return spell_ids
    feature_text = " ".join(character.features).lower()
    matching_ids = []
    for spell_id in spell_ids:
        spell = app.compendium.load_spell(spell_id)
        if spell.name.lower() in feature_text:
            matching_ids.append(spell_id)
    return tuple(matching_ids) or spell_ids


def _party_member_frame(
    app: DnDCombatEngineApp,
    qt,
    character_id: str,
    initiative_results: dict[str, int] | None = None,
    beacon_of_hope_targets: tuple[str, ...] = (),
    bless_targets: tuple[str, ...] = (),
    on_upload_sheet=None,
    on_remove_member=None,
    on_set_initiative=None,
):
    frame_class = getattr(qt.QtWidgets, "QFrame", qt.QtWidgets.QWidget)
    frame = frame_class()
    if hasattr(frame, "setObjectName"):
        frame.setObjectName("PartyMemberFrame")
    _set_frame_style(frame_class, frame)
    layout = qt.QtWidgets.QVBoxLayout(frame)
    try:
        character = app.characters.load(character_id)
    except KeyError:
        layout.addWidget(qt.QtWidgets.QLabel(f"{character_id}\nMissing character data"))
        return frame

    layout.addWidget(
        _party_frame_header(qt, character.name, character_id, beacon_of_hope_targets, bless_targets)
    )
    hp_text = (
        f"HP {character.hit_points.current}/{character.hit_points.maximum}"
        f"  THP {character.hit_points.temporary}"
    )
    layout.addWidget(qt.QtWidgets.QLabel(hp_text))
    progress_class = getattr(qt.QtWidgets, "QProgressBar", None)
    if progress_class is not None:
        progress = progress_class()
        if hasattr(progress, "setRange"):
            progress.setRange(0, character.hit_points.maximum)
        if hasattr(progress, "setValue"):
            progress.setValue(character.hit_points.current)
        if hasattr(progress, "setFormat"):
            progress.setFormat(hp_text)
        layout.addWidget(progress)
    initiative_results = initiative_results or {}
    initiative_value = initiative_results.get(character_id)
    layout.addWidget(qt.QtWidgets.QLabel(_initiative_text(character_id, initiative_results)))
    if on_set_initiative is not None:
        _add_initiative_entry(qt, layout, character_id, on_set_initiative)
    feature_text = _party_frame_feature_text(character.features)
    if feature_text:
        feature_label = qt.QtWidgets.QLabel(feature_text)
        if hasattr(feature_label, "setWordWrap"):
            feature_label.setWordWrap(True)
        layout.addWidget(feature_label)
    condition_text = _party_frame_condition_text(character.conditions)
    if condition_text:
        condition_label = qt.QtWidgets.QLabel(condition_text)
        if hasattr(condition_label, "setWordWrap"):
            condition_label.setWordWrap(True)
        if hasattr(condition_label, "setToolTip"):
            condition_label.setToolTip("Tracked conditions on this party member.")
        layout.addWidget(condition_label)
    _install_party_context_menu(
        qt,
        frame,
        character_id,
        initiative_value,
        on_upload_sheet,
        on_remove_member,
        on_set_initiative,
    )
    return frame


def _party_frame_header(
    qt,
    character_name: str,
    character_id: str,
    beacon_of_hope_targets: tuple[str, ...] = (),
    bless_targets: tuple[str, ...] = (),
):
    header = qt.QtWidgets.QWidget()
    layout = qt.QtWidgets.QHBoxLayout(header)
    layout.addWidget(qt.QtWidgets.QLabel(character_name))
    if hasattr(layout, "addStretch"):
        layout.addStretch(1)
    if character_id in beacon_of_hope_targets:
        layout.addWidget(
            _party_buff_icon(
                qt,
                "HV",
                "BeaconOfHopeBuff",
                "Beacon of Hope: Hope and Vitality. "
                "Wisdom and death saves are bolstered; healing is maximized.",
                "#2f6fed",
                "#8eb3ff",
            )
        )
    if character_id in bless_targets:
        layout.addWidget(
            _party_buff_icon(
                qt,
                "B",
                "BlessBuff",
                "Bless: add 1d4 to attack rolls and saving throws while concentration holds.",
                "#8f6a22",
                "#ffd27a",
            )
        )
    return header


def _party_buff_icon(
    qt,
    text: str,
    object_name: str,
    tooltip: str,
    background: str,
    border: str,
):
    buff_label = qt.QtWidgets.QLabel(text)
    if hasattr(buff_label, "setObjectName"):
        buff_label.setObjectName(object_name)
    if hasattr(buff_label, "setToolTip"):
        buff_label.setToolTip(tooltip)
    if hasattr(buff_label, "setStyleSheet"):
        buff_label.setStyleSheet(
            f"background:{background};color:white;border:1px solid {border};"
            "border-radius:3px;padding:1px 4px;font-weight:bold;"
        )
    return buff_label


def _party_frame_feature_text(features: tuple[str, ...]) -> str:
    """Return a compact combat feature summary for party frames."""
    feature_names = {feature.lower() for feature in _party_frame_feature_candidates(features)}
    visible_features = [
        feature for feature in PARTY_FRAME_FEATURES if feature.lower() in feature_names
    ]
    return ", ".join(visible_features[:3])


def _party_frame_condition_text(conditions) -> str:
    """Return a compact condition summary for party frames."""
    names = []
    for condition in conditions:
        name = getattr(getattr(condition, "name", condition), "value", str(condition))
        if name:
            names.append(str(name).replace("_", " ").title())
    return f"Conditions: {', '.join(names)}" if names else ""


def _party_frame_feature_candidates(features: tuple[str, ...]) -> tuple[str, ...]:
    metadata_prefixes = (
        "background",
        "cantrips",
        "class",
        "class & level",
        "domain spells",
        "player name",
        "species",
    )
    names: list[str] = []
    for feature in features:
        feature_text = feature.strip()
        if not feature_text:
            continue
        lowered = feature_text.lower()
        if lowered.startswith(metadata_prefixes):
            continue
        names.extend(part.strip() for part in feature_text.split(",") if part.strip())
    return tuple(names)


def _actionable_ability_names(features: tuple[str, ...]) -> tuple[str, ...]:
    """Return feature names that should be placeable on the action bar."""
    feature_blob = "\n".join(features).lower()
    names = ["Basic Attack"]
    for ability in ACTIONABLE_ABILITY_FEATURES:
        if ability == "Basic Attack":
            continue
        if ability.lower() in feature_blob:
            names.append(ability)
    return tuple(dict.fromkeys(names))


def _ability_tooltip(feature: str) -> str:
    """Return a short tooltip for an action-ready ability."""
    descriptions = {
        "Basic Attack": "Make a weapon attack with the active character's first weapon.",
        "Attack": "Make a weapon attack with the active character's first weapon.",
        "Sneak Attack": "Add rogue precision damage when Sneak Attack conditions are met.",
        "Divine Smite": "Spend divine power to add radiant damage to a weapon hit.",
        "Great Weapon Master": "Use the heavy-weapon damage feature when available.",
        "Sharpshooter": "Use the ranged-weapon damage feature when available.",
        "Rage": "Use rage-enhanced melee damage when available.",
        "Channel Divinity: Turn Undead": "Present your holy symbol and turn undead creatures.",
        "Channel Divinity: Preserve Life": "Restore hit points to creatures within range.",
    }
    return "\n".join((feature, descriptions.get(feature, "Character ability.")))


def _spell_rank_options(
    app: DnDCombatEngineApp,
    character_id: str | None,
    spell,
) -> tuple[int, ...]:
    if spell.level == 0:
        return (1,)
    slot_levels = []
    if character_id is not None:
        try:
            character = app.characters.load(character_id)
        except KeyError:
            character = None
        if character is not None:
            if ensure_spell_slot_resources(character) and hasattr(app.characters, "save"):
                app.characters.save(character)
            for resource_name, resource in character.resources.items():
                match = re.fullmatch(r"spell_slot_(\d+)", resource_name)
                if match and resource.maximum > 0:
                    slot_level = int(match.group(1))
                    if slot_level >= spell.level:
                        slot_levels.append(slot_level)
    if not slot_levels:
        return (spell.level,)
    highest_slot = max(slot_levels)
    return tuple(range(spell.level, highest_slot + 1))


def _is_valid_attack_name(name: str) -> bool:
    cleaned = name.strip().casefold()
    rejected = {
        "instead",
        "range",
        "reach",
        "notes",
        "attack",
        "attacks",
        "damage",
        "hit",
        "hit dc",
        "hit/dc",
        "dc",
    }
    return bool(cleaned) and cleaned not in rejected


def _spell_rank_button_text(spell_name: str, rank: int, spell_level: int | None = None) -> str:
    if spell_level == 0 or rank <= 0:
        return f"{spell_name} (Cantrip)"
    return f"{spell_name} (Level {rank})"


def _inventory_item_tooltip(item: InventoryItem) -> str:
    """Return an inventory tooltip with stack, weight, and use notes."""
    lines = [
        item.name,
        f"Category: {item.category.value.replace('_', ' ').title()}",
        f"Quantity: {item.quantity}",
    ]
    if item.weight:
        lines.append(f"Weight: {item.weight:g} lb each ({item.total_weight:g} lb total)")
    price_cp = item.purchase_price_cp or _default_purchase_price_cp(item)
    if price_cp:
        lines.append(f"Sell Price: {_currency_price_text(price_cp // 2)}")
    if item.tags:
        lines.append(f"Tags: {', '.join(item.tags)}")
    if item.notes:
        lines.append(_wrap_tooltip_text(item.notes))
    if item.category.value == "consumable" or "potion" in item.tags or "potion" in item.item_id:
        lines.append("Right-click to consume one.")
    return "\n".join(lines)


def _default_purchase_price_cp(item: InventoryItem) -> int:
    defaults = {
        "potion_of_healing_greater": 50_000,
        "potion_of_greater_healing": 50_000,
    }
    return defaults.get(item.item_id, 0)


def _currency_price_text(amount_cp: int) -> str:
    purse = CurrencyPurse.from_cp(amount_cp)
    parts = []
    for label, value in (("PP", purse.pp), ("GP", purse.gp), ("SP", purse.sp), ("CP", purse.cp)):
        if value:
            parts.append(f"{value}{label}")
    return " ".join(parts) if parts else "0CP"


def _proficiency_bonus(level: int) -> int:
    return 2 + max(level - 1, 0) // 4


def _damage_profile_text(damage) -> str:
    return ", ".join(
        f"{component.dice} {component.damage_type.value}" for component in damage.components
    )


def _wrap_tooltip_text(value: str, width: int = 72) -> str:
    return "\n".join(textwrap.wrap(value, width=width)) or value


def _initiative_text(
    character_id: str | int | None,
    initiative_results: dict[str, int] | None = None,
) -> str:
    """Return initiative roll and party-order text for a party frame."""
    if isinstance(character_id, int) and initiative_results is None:
        return f"Initiative: {character_id} | Position: 1"
    if character_id is None and initiative_results is None:
        return "Initiative: - | Position: -"
    results = initiative_results or {}
    character_key = str(character_id)
    value = results.get(character_key)
    if value is None:
        return "Initiative: - | Position: -"
    ordered = sorted(results.items(), key=lambda item: (-item[1], item[0]))
    position = next(
        (
            index
            for index, (result_id, _) in enumerate(ordered, start=1)
            if result_id == character_key
        ),
        None,
    )
    position_text = str(position) if position is not None else "-"
    return f"Initiative: {value} | Position: {position_text}"


def _add_initiative_entry(qt, layout, character_id: str, on_set_initiative) -> None:
    row = qt.QtWidgets.QWidget()
    row_layout = qt.QtWidgets.QHBoxLayout(row)
    input_box = qt.QtWidgets.QLineEdit("")
    if hasattr(input_box, "setPlaceholderText"):
        input_box.setPlaceholderText("Initiative roll")
    set_button = qt.QtWidgets.QPushButton("Set")

    def submit() -> None:
        value = _parse_initiative_value(input_box.text())
        if value is not None:
            on_set_initiative(character_id, value)

    set_button.clicked.connect(submit)
    row_layout.addWidget(input_box)
    row_layout.addWidget(set_button)
    layout.addWidget(row)


def _parse_initiative_value(value: str) -> int | None:
    value = value.strip()
    if not re.fullmatch(r"-?\d{1,3}", value):
        return None
    return int(value)


def _install_party_context_menu(
    qt,
    frame,
    character_id: str,
    initiative_value: int | None,
    on_upload_sheet,
    on_remove_member,
    on_set_initiative,
) -> None:
    if not any((on_upload_sheet, on_remove_member, on_set_initiative)):
        return
    if not hasattr(frame, "setContextMenuPolicy") or not hasattr(
        frame,
        "customContextMenuRequested",
    ):
        return
    policy = getattr(getattr(qt.QtCore.Qt, "ContextMenuPolicy", None), "CustomContextMenu", None)
    if policy is None:
        policy = getattr(qt.QtCore.Qt, "CustomContextMenu", None)
    if policy is None:
        return
    frame.setContextMenuPolicy(policy)
    frame.customContextMenuRequested.connect(
        lambda position: _show_party_context_menu(
            qt,
            frame,
            position,
            character_id,
            initiative_value,
            on_upload_sheet,
            on_remove_member,
            on_set_initiative,
        )
    )


def _show_party_context_menu(
    qt,
    frame,
    position,
    character_id: str,
    initiative_value: int | None,
    on_upload_sheet,
    on_remove_member,
    on_set_initiative,
) -> None:
    menu_class = getattr(qt.QtWidgets, "QMenu", None)
    if menu_class is None:
        return
    menu = menu_class(frame)
    if on_upload_sheet is not None:
        upload_menu = menu.addMenu("Upload Character Sheet")
        _add_menu_action(
            upload_menu,
            "PDF",
            lambda item_id: on_upload_sheet(item_id, "pdf"),
            character_id,
        )
        _add_menu_action(
            upload_menu,
            "URL",
            lambda item_id: on_upload_sheet(item_id, "url"),
            character_id,
        )
    _add_menu_action(menu, "Remove Player from Party", on_remove_member, character_id)
    if on_set_initiative is not None:
        action = menu.addAction("Enter Initiative Roll")
        if hasattr(action, "triggered"):
            action.triggered.connect(
                lambda checked=False: _prompt_and_set_initiative(
                    qt,
                    frame,
                    character_id,
                    initiative_value,
                    on_set_initiative,
                )
            )
    global_position = frame.mapToGlobal(position) if hasattr(frame, "mapToGlobal") else position
    if hasattr(menu, "exec"):
        menu.exec(global_position)
    elif hasattr(menu, "exec_"):
        menu.exec_(global_position)


def _add_menu_action(menu, label: str, callback, character_id: str) -> None:
    if callback is None:
        return
    action = menu.addAction(label)
    if hasattr(action, "triggered"):
        action.triggered.connect(lambda checked=False: callback(character_id))


def _prompt_and_set_initiative(
    qt,
    parent,
    character_id: str,
    current_value: int | None,
    on_set_initiative,
) -> None:
    value = _ask_initiative_roll(qt, parent, current_value)
    if value is not None:
        on_set_initiative(character_id, value)


def _ask_initiative_roll(qt, parent, current_value: int | None) -> int | None:
    dialog = getattr(qt.QtWidgets, "QInputDialog", None)
    if dialog is None:
        return None
    selected = dialog.getInt(
        parent,
        "Initiative Roll",
        "Initiative roll result:",
        current_value or 0,
        -99,
        999,
        1,
    )
    if isinstance(selected, tuple):
        value, accepted = selected
        return int(value) if accepted else None
    return int(selected) if selected is not None else None


def _set_frame_style(frame_class, frame) -> None:
    shape = getattr(getattr(frame_class, "Shape", None), "StyledPanel", None)
    shadow = getattr(getattr(frame_class, "Shadow", None), "Raised", None)
    if shape is None:
        shape = getattr(frame_class, "StyledPanel", None)
    if shadow is None:
        shadow = getattr(frame_class, "Raised", None)
    if shape is not None and hasattr(frame, "setFrameShape"):
        frame.setFrameShape(shape)
    if shadow is not None and hasattr(frame, "setFrameShadow"):
        frame.setFrameShadow(shadow)


def _activate_action_button(
    session: ActionBarSession,
    on_activate,
    slot: int,
    shift_pressed: bool,
) -> str:
    if on_activate is not None:
        return str(on_activate(slot, shift_pressed))
    return session.activate(slot)


def _action_bar_button_class(qt, session: ActionBarSession, on_activate=None):
    base_class = qt.QtWidgets.QPushButton

    class ShiftRemovableActionButton(base_class):
        def __init__(self, text: str, slot: int) -> None:
            super().__init__(text)
            self._dnd_slot = slot

        def mousePressEvent(self, event) -> None:  # noqa: N802
            if _is_shift_right_click(qt, event):
                session.remove(self._dnd_slot)
                if hasattr(event, "accept"):
                    event.accept()
                return
            if _is_shift_left_click(qt, event):
                _activate_action_button(session, on_activate, self._dnd_slot, True)
                if hasattr(event, "accept"):
                    event.accept()
                return
            super().mousePressEvent(event)

    return ShiftRemovableActionButton


def _is_shift_left_click(qt, event) -> bool:
    button = event.button() if hasattr(event, "button") else None
    modifiers = event.modifiers() if hasattr(event, "modifiers") else None
    mouse_button = getattr(getattr(qt.QtCore.Qt, "MouseButton", None), "LeftButton", None)
    keyboard_modifier = getattr(
        getattr(qt.QtCore.Qt, "KeyboardModifier", None),
        "ShiftModifier",
        None,
    )
    if mouse_button is None:
        mouse_button = getattr(qt.QtCore.Qt, "LeftButton", None)
    if keyboard_modifier is None:
        keyboard_modifier = getattr(qt.QtCore.Qt, "ShiftModifier", None)
    if mouse_button is None or keyboard_modifier is None or modifiers is None:
        return False
    return button == mouse_button and bool(modifiers & keyboard_modifier)


def _is_shift_right_click(qt, event) -> bool:
    button = event.button() if hasattr(event, "button") else None
    modifiers = event.modifiers() if hasattr(event, "modifiers") else None
    mouse_button = getattr(getattr(qt.QtCore.Qt, "MouseButton", None), "RightButton", None)
    keyboard_modifier = getattr(
        getattr(qt.QtCore.Qt, "KeyboardModifier", None),
        "ShiftModifier",
        None,
    )
    if mouse_button is None:
        mouse_button = getattr(qt.QtCore.Qt, "RightButton", None)
    if keyboard_modifier is None:
        keyboard_modifier = getattr(qt.QtCore.Qt, "ShiftModifier", None)
    if mouse_button is None or keyboard_modifier is None or modifiers is None:
        return False
    return button == mouse_button and bool(modifiers & keyboard_modifier)


def _action_id(name: str) -> str:
    return name.lower().replace(" ", "_").replace("'", "")
