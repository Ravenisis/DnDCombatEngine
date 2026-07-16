"""Headless PySide6 checks exercised by the full cross-platform test suite."""

from __future__ import annotations

import os
import shutil
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
    engine = create_app(data_root)
    window = main_window.create_main_window(engine)
    try:
        main_window._open_preferences_window(window, qt, engine)
        application.processEvents()

        popup = window._dnd_named_popups["preferences"]  # noqa: SLF001
        assert popup.parent() is window
        assert not popup.isWindow()
        assert popup.findChild(qt.QtWidgets.QComboBox) is not None
        assert any(
            label.text() == "GitHub Bug Report Upload"
            for label in popup.findChildren(qt.QtWidgets.QLabel)
        )
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


@pytest.mark.gui
def test_multiline_input_tab_and_backtab_follow_focus_order() -> None:
    """Tab leaves multiline input and Shift+Tab returns to it without indentation."""
    pytest.importorskip("PySide6")

    from PySide6 import QtTest

    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    form = qt.QtWidgets.QWidget()
    layout = qt.QtWidgets.QVBoxLayout(form)
    previous = qt.QtWidgets.QLineEdit()
    notes = qt.QtWidgets.QTextEdit()
    following = qt.QtWidgets.QLineEdit()
    main_window._enable_tab_focus_navigation(notes)  # noqa: SLF001
    layout.addWidget(previous)
    layout.addWidget(notes)
    layout.addWidget(following)
    form.show()
    notes.setFocus()
    application.processEvents()

    QtTest.QTest.keyClick(notes, qt.QtCore.Qt.Key.Key_Tab)
    application.processEvents()
    assert following.hasFocus()
    assert notes.toPlainText() == ""

    QtTest.QTest.keyClick(
        following,
        qt.QtCore.Qt.Key.Key_Tab,
        qt.QtCore.Qt.KeyboardModifier.ShiftModifier,
    )
    application.processEvents()
    assert notes.hasFocus()
    form.close()


@pytest.mark.gui
def test_srd_item_selector_filters_contains_matches() -> None:
    """Typing in the SRD selector narrows its completion popup without insertion."""
    pytest.importorskip("PySide6")

    from PySide6 import QtTest

    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    selector = qt.QtWidgets.QComboBox()
    selector.addItems(
        (
            "Custom Item",
            "Potion of Healing",
            "Potion of Flying",
            "Plate Armor",
        )
    )
    main_window._configure_srd_item_filter(qt, selector)  # noqa: SLF001
    selector.show()
    selector.lineEdit().clear()
    QtTest.QTest.keyClicks(selector.lineEdit(), "potion")
    application.processEvents()

    completer = selector.completer()
    model = completer.completionModel()
    matches = [str(model.data(model.index(row, 0))) for row in range(model.rowCount())]
    assert selector.isEditable()
    assert selector.insertPolicy() == qt.QtWidgets.QComboBox.InsertPolicy.NoInsert
    assert matches == ["Potion of Healing", "Potion of Flying"]
    selector.close()


@pytest.mark.gui
def test_escape_closes_money_log_from_focused_text_area() -> None:
    """The Money Log Escape shortcut works while its read-only log has focus."""
    pytest.importorskip("PySide6")

    from PySide6 import QtTest

    from dnd_combat_engine.gui import widgets
    from dnd_combat_engine.gui.qt import load_qt
    from dnd_combat_engine.models import CurrencyPurse

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    parent = qt.QtWidgets.QWidget()
    parent.resize(500, 400)
    parent.show()
    dialog = widgets._show_money_log(  # noqa: SLF001
        qt,
        parent,
        "Ravenisis",
        ["Opening balance: 1GP"],
        {"purse": CurrencyPurse(gp=1)},
    )
    output = dialog.findChild(qt.QtWidgets.QTextEdit)
    output.setFocus()
    application.processEvents()

    QtTest.QTest.keyClick(output, qt.QtCore.Qt.Key.Key_Escape)
    application.processEvents()

    assert not dialog.isVisible()
    parent.close()


@pytest.mark.gui
def test_money_log_escape_closes_child_before_inventory_window() -> None:
    """Escape closes the Money Log first and Inventory on the next press."""
    pytest.importorskip("PySide6")

    from PySide6 import QtTest

    from dnd_combat_engine.app import create_app
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    engine = create_app(Path(__file__).resolve().parents[1] / "data")
    window = main_window.create_main_window(engine)
    window.show()
    try:
        state = window._dnd_campaign_state  # noqa: SLF001
        state.party_leader_character_id = "ravenisis"
        main_window._open_inventory_window(window, qt, engine, state)  # noqa: SLF001
        application.processEvents()
        inventory = window._dnd_named_popups["inventory"]  # noqa: SLF001
        money_log_button = next(
            button
            for button in inventory.findChildren(qt.QtWidgets.QPushButton)
            if button.text() == "Money Log"
        )
        money_log_button.click()
        application.processEvents()
        money_log = inventory.findChild(qt.QtWidgets.QWidget, "MoneyLogPopup")
        assert money_log is not None
        assert money_log.isVisible()

        QtTest.QTest.keyClick(inventory, qt.QtCore.Qt.Key.Key_Escape)
        application.processEvents()

        assert not money_log.isVisible()
        assert inventory.isVisible()
        assert window._dnd_named_popups["inventory"] is inventory  # noqa: SLF001

        QtTest.QTest.keyClick(inventory, qt.QtCore.Qt.Key.Key_Escape)
        application.processEvents()

        assert "inventory" not in window._dnd_named_popups  # noqa: SLF001
    finally:
        window.close()


@pytest.mark.gui
def test_consuming_last_item_refreshes_open_inventory_immediately(tmp_path: Path) -> None:
    """Using the last consumable removes its icon without reopening Inventory."""
    pytest.importorskip("PySide6")

    from PySide6 import QtTest

    from dnd_combat_engine.app import create_app
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    source_data = Path(__file__).resolve().parents[1] / "data"
    test_data = tmp_path / "data"
    shutil.copytree(source_data, test_data)
    engine = create_app(test_data)
    window = main_window.create_main_window(engine)
    window.show()
    try:
        state = window._dnd_campaign_state  # noqa: SLF001
        state.party_leader_character_id = "ravenisis"
        main_window._open_inventory_window(window, qt, engine, state)  # noqa: SLF001
        application.processEvents()
        inventory = window._dnd_named_popups["inventory"]  # noqa: SLF001
        potion_buttons = [
            button
            for button in inventory.findChildren(qt.QtWidgets.QPushButton)
            if "Potion of Healing (Greater)" in button.toolTip()
        ]
        assert len(potion_buttons) == 1

        QtTest.QTest.mouseClick(
            potion_buttons[0],
            qt.QtCore.Qt.MouseButton.RightButton,
        )
        application.processEvents()

        assert not any(
            "Potion of Healing (Greater)" in button.toolTip()
            for button in inventory.findChildren(qt.QtWidgets.QPushButton)
        )
        character = engine.characters.load("ravenisis")
        assert engine.inventory.quantity(character, "potion_of_healing_greater") == 0
    finally:
        window.close()


@pytest.mark.gui
def test_polyhedral_dice_bar_rolls_into_combat_workspace() -> None:
    """Click a visual die and verify its result reaches the shared workspace."""
    pytest.importorskip("PySide6")

    from dnd_combat_engine.app import create_app
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    data_root = Path(__file__).resolve().parents[1] / "data"
    engine = create_app(data_root)
    window = main_window.create_main_window(engine)
    try:
        die_button = window.findChild(qt.QtWidgets.QToolButton, "DiceRollButton_d8")
        assert die_button is not None
        die_button.click()
        application.processEvents()

        assert "d8 roll:" in window._dnd_central.toPlainText()  # noqa: SLF001
        assert window._dnd_campaign_state.last_dice_notation == "1d8"  # noqa: SLF001

        state = window._dnd_campaign_state  # noqa: SLF001
        state.party_leader_character_id = "ravenisis"
        main_window._refresh_campaign_docks(window, qt, engine, state)  # noqa: SLF001
        initiative_button = window.findChild(
            qt.QtWidgets.QPushButton,
            "InitiativeRollButton",
        )
        assert initiative_button is not None
        assert "+1" in initiative_button.text()
        initiative_button.click()
        application.processEvents()

        assert "Ravenisis initiative:" in window._dnd_central.toPlainText()  # noqa: SLF001
        assert state.party_initiative["ravenisis"] >= 2
    finally:
        window.close()


@pytest.mark.gui
def test_shift_number_shortcut_rolls_action_bar_check(monkeypatch) -> None:
    """Shift+1 follows the same hit-check path as Shift+left-click."""
    pytest.importorskip("PySide6")

    from PySide6 import QtTest

    from dnd_combat_engine.app import create_app
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt
    from dnd_combat_engine.models import ActionBarActionKind, ActionBarButton

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    data_root = Path(__file__).resolve().parents[1] / "data"
    engine = create_app(data_root)
    window = main_window.create_main_window(engine)
    try:
        monkeypatch.setattr(main_window, "_record_campaign_activity", lambda *args: None)
        state = window._dnd_campaign_state  # noqa: SLF001
        state.party_leader_character_id = "ravenisis"
        session = window._dnd_action_bar_session  # noqa: SLF001
        session.place(
            ActionBarButton(
                1,
                ActionBarActionKind.ABILITY,
                "handaxe",
                "Handaxe",
            )
        )
        window.show()
        window.activateWindow()
        application.processEvents()

        QtTest.QTest.keyClick(
            window,
            qt.QtCore.Qt.Key.Key_1,
            qt.QtCore.Qt.KeyboardModifier.ShiftModifier,
        )
        application.processEvents()

        workspace = window._dnd_central.toPlainText()  # noqa: SLF001
        assert "Ravenisis rolls Handaxe" in workspace
        assert "1d20" in workspace
    finally:
        window.close()


@pytest.mark.gui
def test_equipment_popup_renders_slots_stats_and_no_dice_menu() -> None:
    """The Character menu opens equipment while the obsolete Dice menu stays hidden."""
    pytest.importorskip("PySide6")

    from dnd_combat_engine.app import create_app
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.qt import load_qt
    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    data_root = Path(__file__).resolve().parents[1] / "data"
    engine = create_app(data_root)
    window = main_window.create_main_window(engine)
    try:
        state = window._dnd_campaign_state  # noqa: SLF001
        state.party_leader_character_id = "ravenisis"
        main_window._open_equipment_window(window, qt, engine, state)  # noqa: SLF001
        application.processEvents()

        popup = window._dnd_named_popups["equipment"]  # noqa: SLF001
        assert popup.findChild(qt.QtWidgets.QLabel, "EquipmentBodyOutline") is not None
        assert popup.findChild(qt.QtWidgets.QPushButton, "EquipmentSlot_main_hand") is not None
        assert popup.findChild(qt.QtWidgets.QTableWidget, "EquipmentStatsTable") is not None
        menu_labels = [action.text() for action in window.menuBar().actions()]
        assert "Character" in menu_labels
        assert "Dice" not in menu_labels
    finally:
        window.close()


@pytest.mark.gui
def test_equipped_item_uses_inventory_icon_and_rich_tooltip() -> None:
    """Occupied equipment slots show icons while names and rules remain discoverable."""
    pytest.importorskip("PySide6")

    from dnd_combat_engine.gui import equipment
    from dnd_combat_engine.gui.qt import load_qt
    from dnd_combat_engine.models import EquipmentSlot, InventoryItem, ItemCategory

    qt = load_qt()
    qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    item = InventoryItem(
        "warhammer",
        "Warhammer",
        weight=5,
        category=ItemCategory.WEAPON,
        notes="Versatile weapon. Damage: 1d8 or 1d10 when wielded with two hands.",
        tags=("versatile", "damage:1d8"),
        purchase_price_cp=1500,
        equipped_slot=EquipmentSlot.MAIN_HAND,
    )

    button = equipment._equipment_slot_button(  # noqa: SLF001
        qt,
        EquipmentSlot.MAIN_HAND,
        item,
        (),
        None,
        None,
    )

    assert button.text() == "Main Hand"
    assert not button.icon().isNull()
    assert button.iconSize() == qt.QtCore.QSize(40, 40)
    assert "Warhammer" in button.toolTip()
    assert "Weight: 5 lb" in button.toolTip()
    assert "Versatile weapon" in button.toolTip()
    assert button.accessibleName() == "Main Hand: Warhammer"


@pytest.mark.gui
def test_character_tool_windows_restore_geometry_and_escape_closes() -> None:
    """Spellbook, inventory, and equipment remain movable and remember placement."""
    pytest.importorskip("PySide6")

    from PySide6 import QtTest

    from dnd_combat_engine.app import create_app
    from dnd_combat_engine.gui import main_window
    from dnd_combat_engine.gui.overlays import SETTINGS_APPLICATION, SETTINGS_ORGANIZATION
    from dnd_combat_engine.gui.qt import load_qt

    qt = load_qt()
    application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
    settings = qt.QtCore.QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    keys = ("spellbook", "inventory", "equipment")
    for key in keys:
        settings.remove(f"tool_windows/{key}/geometry")
    data_root = Path(__file__).resolve().parents[1] / "data"
    engine = create_app(data_root)
    window = main_window.create_main_window(engine)
    window.show()
    try:
        state = window._dnd_campaign_state  # noqa: SLF001
        state.party_leader_character_id = "ravenisis"
        openers = {
            "spellbook": lambda: main_window._open_spellbook_window(  # noqa: SLF001
                window, qt, engine, state
            ),
            "inventory": lambda: main_window._open_inventory_window(  # noqa: SLF001
                window, qt, engine, state
            ),
            "equipment": lambda: main_window._open_equipment_window(  # noqa: SLF001
                window, qt, engine, state
            ),
        }
        expected = {}
        for index, key in enumerate(keys):
            openers[key]()
            application.processEvents()
            popup = window._dnd_named_popups[key]  # noqa: SLF001
            assert popup.isWindow()
            assert popup.windowFlags() & qt.QtCore.Qt.WindowType.Tool
            assert popup.windowFlags() & qt.QtCore.Qt.WindowType.WindowCloseButtonHint
            position = qt.QtCore.QPoint(15 + index * 10, 20 + index * 10)
            size = qt.QtCore.QSize(700 + index * 20, 640 + index * 20)
            popup.move(position)
            popup.resize(size)
            expected[key] = (position, size)
            popup.close()
            application.processEvents()

        for key in keys:
            openers[key]()
            application.processEvents()
            popup = window._dnd_named_popups[key]  # noqa: SLF001
            position, size = expected[key]
            assert abs(popup.pos().x() - position.x()) <= 5
            assert abs(popup.pos().y() - position.y()) <= 5
            assert popup.size() == size
            QtTest.QTest.keyClick(popup, qt.QtCore.Qt.Key.Key_Escape)
            application.processEvents()
            assert key not in window._dnd_named_popups  # noqa: SLF001
    finally:
        window.close()
        for key in keys:
            settings.remove(f"tool_windows/{key}/geometry")
