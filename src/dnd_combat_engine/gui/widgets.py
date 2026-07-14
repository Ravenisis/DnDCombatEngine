"""PySide6 widgets for the desktop GUI."""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp
from dnd_combat_engine.gui import campaign_panels as _campaign_panels
from dnd_combat_engine.gui import combat_panels as _combat_panels
from dnd_combat_engine.gui import inventory as _inventory
from dnd_combat_engine.gui import spellbook as _spellbook
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.gui.editors import (
    add_character_to_encounter,
    add_monster_to_encounter,
    advance_encounter_round,
    complete_encounter,
    remove_participant_from_encounter,
    start_encounter,
)
from dnd_combat_engine.gui.overlays import (
    create_embedded_popup,
    show_embedded_popup,
)
from dnd_combat_engine.gui.panels import (
    encounter_participant_rows,
    encounter_rows,
)
from dnd_combat_engine.models.action_bar import ActionBar, ActionBarActionKind, ActionBarButton
from dnd_combat_engine.models.currency import CurrencyPurse
from dnd_combat_engine.models.inventory import InventoryItem, ItemCategory
from dnd_combat_engine.models.spell_slots import (
    ensure_spell_slot_resources,
    ensure_spell_slot_resources_for_level,
)

CampaignEditorWidget = _campaign_panels.CampaignEditorWidget
CampaignWidget = _campaign_panels.CampaignWidget
PartyFramesWidget = _campaign_panels.PartyFramesWidget
TargetPanelWidget = _campaign_panels.TargetPanelWidget
_campaign_character_selector = _campaign_panels._campaign_character_selector
_monster_target_current_hp = _campaign_panels._monster_target_current_hp
_selector_text = _campaign_panels._selector_text
_target_button_text = _campaign_panels._target_button_text
_target_panel_references = _campaign_panels._target_panel_references
InventoryWidget = _inventory.InventoryWidget
AttackPanelWidget = _combat_panels.AttackPanelWidget
CampaignActivityWidget = _combat_panels.CampaignActivityWidget
CharacterSheetWidget = _combat_panels.CharacterSheetWidget
CombatLogWidget = _combat_panels.CombatLogWidget
DiceTrayWidget = _combat_panels.DiceTrayWidget
EncounterEditorWidget = _combat_panels.EncounterEditorWidget
EncounterTrackerWidget = _combat_panels.EncounterTrackerWidget
InitiativeWidget = _combat_panels.InitiativeWidget
_quick_attack_message = _combat_panels._quick_attack_message
SpellbookWidget = _spellbook.SpellbookWidget
_actionable_ability_names_for_tab = _spellbook._actionable_ability_names_for_tab
_add_spellbook_tab = _spellbook._add_spellbook_tab
_attack_names_for_character = _spellbook._attack_names_for_character
_is_channel_divinity_name = _spellbook._is_channel_divinity_name
_spellbook_tab = _spellbook._spellbook_tab
_spellbook_tab_add_widget = _spellbook._spellbook_tab_add_widget
_spellbook_tab_finish = _spellbook._spellbook_tab_finish
_spellbook_tabs = _spellbook._spellbook_tabs

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
            modifier = _saving_throw_modifier(character, ability)
            button = qt.QtWidgets.QPushButton(f"{label}\n{modifier:+d}")
            proficient = ability in proficiencies
            if proficient and hasattr(button, "setStyleSheet"):
                button.setStyleSheet("border-left: 4px solid #4f8cff;")
            if hasattr(button, "setToolTip"):
                bonus_text = (
                    "Imported sheet modifier"
                    if ability in character.saving_throw_modifiers
                    else "Ability modifier plus proficiency"
                    if proficient
                    else "Ability modifier"
                )
                button.setToolTip(
                    f"{ability.title()} save: d20 {modifier:+d}. "
                    f"{bonus_text}. Shift-click to roll with advantage."
                )
            button.clicked.connect(
                lambda checked=False, save=ability: _trigger_saving_throw(
                    on_roll,
                    save,
                    _shift_pressed(qt),
                )
                if on_roll is not None
                else None
            )
            try:
                layout.addWidget(button, row, column)
            except TypeError:
                layout.addWidget(button)
        return widget


























def _inventory_header(
    qt,
    character_name: str,
    purse: CurrencyPurse,
    on_currency_change,
    on_add_item=None,
    money_log_entries: list[str] | None = None,
    money_log_current: dict | None = None,
):
    widget = qt.QtWidgets.QWidget()
    grid_class = getattr(qt.QtWidgets, "QGridLayout", qt.QtWidgets.QVBoxLayout)
    layout = grid_class(widget)
    title = qt.QtWidgets.QLabel(f"Inventory: {character_name}")
    if on_add_item is not None:
        add_item_button = qt.QtWidgets.QPushButton("Add Item")
        if hasattr(add_item_button, "setToolTip"):
            add_item_button.setToolTip("Manually add an item stack to this inventory.")
        add_item_button.clicked.connect(lambda checked=False: on_add_item())
    else:
        add_item_button = None
    money_log = money_log_entries
    if money_log is None:
        money_log = [f"Opening balance: {_currency_price_text(purse.total_cp)}"]
    money_log_button = qt.QtWidgets.QPushButton("Money Log")
    if hasattr(money_log_button, "setToolTip"):
        money_log_button.setToolTip("Show currency changes made while this inventory is open.")
    ledger = qt.QtWidgets.QLineEdit()
    if hasattr(ledger, "setPlaceholderText"):
        ledger.setPlaceholderText("1PP 100GP")
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
    boxes = _currency_boxes(qt, purse)
    currency_grid = _currency_box_grid(qt, boxes)
    current = money_log_current if money_log_current is not None else {"purse": purse}
    current["purse"] = purse

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
    _inventory_header_add(layout, title, 0, 0)
    if add_item_button is not None:
        _inventory_header_add(layout, add_item_button, 0, 1)
    _inventory_header_add(layout, money_log_button, 0, 2)
    _inventory_header_add(layout, ledger, 1, 0, 1, 2)
    _inventory_header_add(layout, buttons, 1, 2)
    _inventory_header_add(layout, currency_grid, 0, 3, 2, 1)
    if hasattr(layout, "setColumnStretch"):
        layout.setColumnStretch(0, 1)
    return widget


def _inventory_header_add(
    layout,
    widget,
    row: int,
    column: int,
    row_span: int = 1,
    column_span: int = 1,
) -> None:
    """Add a responsive inventory-header cell on real and fallback Qt layouts."""
    try:
        layout.addWidget(widget, row, column, row_span, column_span)
    except TypeError:
        layout.addWidget(widget)


def _show_money_log(qt, parent, character_name: str, entries: list[str], current: dict):
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    if dialog_class is None:
        return None
    dialog = create_embedded_popup(qt, parent)
    if dialog is None:
        return None
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
    show_embedded_popup(parent, dialog)
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
                if _is_shift_right_click(qt, event) and on_sell is not None:
                    _sell_inventory_button_item(self, item, on_sell)
                    if hasattr(event, "accept"):
                        event.accept()
                    return
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
    names.extend(_inventory_family_icon_candidates(item))
    names.extend(_inventory_tag_icon_candidates(item))
    return tuple(dict.fromkeys(names))


def _inventory_family_icon_candidates(item: InventoryItem) -> tuple[str, ...]:
    """Return icon candidates inferred from common SRD item families."""
    item_id = item.item_id
    tags = set(item.tags)
    candidates: list[str] = []
    prefix_icons = (
        ("amulet_", "amulet"),
        ("bag_of_", "magic_container"),
        ("belt_", "belt"),
        ("boots_", "boots"),
        ("bracers_", "bracers"),
        ("cloak_", "cloak"),
        ("cube_", "force_item"),
        ("figurine_", "figurine"),
        ("gem_of_", "gemstone"),
        ("gloves_", "gloves"),
        ("goggles_", "goggles"),
        ("hat_", "clothing"),
        ("helm_", "helm"),
        ("horn_", "horn_magic"),
        ("instrument_of_the_bards_", "bard_instrument"),
        ("ioun_stone_", "ioun_stone"),
        ("manual_", "manual"),
        ("oil_", "potion"),
        ("periapt_", "amulet"),
        ("potion_", "potion"),
        ("ring_", "ring"),
        ("robe_", "robe_magic"),
        ("rod_", "rod"),
        ("staff_", "staff_magic"),
        ("talisman_", "talisman"),
        ("tome_", "tome"),
        ("wand_", "wand"),
    )
    for prefix, icon in prefix_icons:
        if item_id.startswith(prefix):
            candidates.append(icon)
            break
    if "cursed" in tags:
        candidates.append("cursed")
    if item.category == ItemCategory.ARMOR and "magic item" in tags:
        candidates.append("magic_armor")
    if item.category == ItemCategory.WEAPON and "magic item" in tags:
        candidates.append("magic_weapon")
    if "container" in tags and "magic item" in tags:
        candidates.append("magic_container")
    if "gemstone" in tags or "gem" in tags:
        candidates.append("gemstone")
    if "art object" in tags:
        candidates.append("art_object")
    if "manual" in tags:
        candidates.append("manual")
    if "tome" in tags:
        candidates.append("tome")
    if "jewelry" in tags and not any(icon in candidates for icon in ("amulet", "ring")):
        candidates.append("jewelry")
    return tuple(dict.fromkeys(candidates))


def _inventory_tag_icon_candidates(item: InventoryItem) -> tuple[str, ...]:
    tag_icons = {
        "ammunition": "ammunition",
        "arcane focus": "focus",
        "art object": "art_object",
        "belt": "belt",
        "book": "book",
        "bracers": "bracers",
        "card": "game",
        "clothing": "clothing",
        "container": "container",
        "cursed": "trap",
        "druidic focus": "focus",
        "elemental": "focus",
        "figurine": "figurine",
        "focus": "focus",
        "force": "force_item",
        "gauntlets": "gauntlets",
        "gaming set": "game",
        "gem": "gemstone",
        "gemstone": "gemstone",
        "goggles": "goggles",
        "healing": "potion",
        "holy symbol": "holy_symbol",
        "horn": "horn_magic",
        "jewelry": "jewelry",
        "large vehicle": "vehicle",
        "light": "light_source",
        "light_source": "light_source",
        "magic item": "treasure",
        "manual": "manual",
        "mount": "mount",
        "musical instrument": "instrument",
        "portal": "focus",
        "potion": "potion",
        "ring": "ring",
        "rod": "rod",
        "scroll": "scroll",
        "service": "treasure",
        "summoning": "figurine",
        "talisman": "talisman",
        "tome": "tome",
        "trade good": "treasure",
        "vehicle": "vehicle",
        "wand": "wand",
        "weapon": "weapon",
    }
    return tuple(tag_icons[tag] for tag in item.tags if tag in tag_icons)


def _is_right_click(qt, event) -> bool:
    button = event.button() if hasattr(event, "button") else None
    mouse_button = getattr(getattr(qt.QtCore.Qt, "MouseButton", None), "RightButton", None)
    if mouse_button is None:
        mouse_button = getattr(qt.QtCore.Qt, "RightButton", None)
    return mouse_button is not None and button == mouse_button


class _LegacyEncounterTrackerWidget:
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


class _LegacyEncounterEditorWidget:
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
                    "Click to cast; Shift+click rolls the action check with its modifier.",
                    "Shift+right-click to remove.",
                )
            )
    lines = [
        f"{action.name} rank {action.rank}",
        f"Type: {action.kind.value.title()}",
        f"Shortcut: {hotkey}",
    ]
    if action.kind == ActionBarActionKind.SPELL:
        lines.append("Click to cast; Shift+click rolls the action check with its modifier.")
    else:
        lines.append("Click to use; Shift+click rolls the action check with its modifier.")
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
    imported_spell_names = {name.casefold() for name in character.spells}
    feature_text = " ".join(character.features).lower()
    matching_ids = []
    for spell_id in spell_ids:
        spell = app.compendium.load_spell(spell_id)
        if spell.name.casefold() in imported_spell_names or spell.name.casefold() in feature_text:
            matching_ids.append(spell_id)
    if character.spells:
        return tuple(matching_ids)
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
        lines.append("Shift+right-click to sell one.")
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


def _saving_throw_modifier(character, ability: str) -> int:
    imported = character.saving_throw_modifiers.get(ability.lower())
    if imported is not None:
        return imported
    proficient = ability.lower() in {
        name.lower() for name in character.saving_throw_proficiencies
    }
    proficiency = _proficiency_bonus(character.level) if proficient else 0
    return character.abilities.modifier(ability) + proficiency


def _trigger_saving_throw(on_roll, ability: str, advantage: bool):
    try:
        return on_roll(ability, advantage)
    except TypeError:
        return on_roll(ability)


def _shift_pressed(qt) -> bool:
    application = getattr(qt.QtWidgets, "QApplication", None)
    if application is None or not hasattr(application, "keyboardModifiers"):
        return False
    modifiers = application.keyboardModifiers()
    shift = getattr(getattr(qt.QtCore.Qt, "KeyboardModifier", None), "ShiftModifier", None)
    if shift is None:
        shift = getattr(qt.QtCore.Qt, "ShiftModifier", None)
    return bool(shift is not None and modifiers & shift)


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
