"""Character equipment screen with body-positioned drop slots."""

from __future__ import annotations

from typing import Any

from dnd_combat_engine.gui.drag_drop import item_id_from_mime
from dnd_combat_engine.models import EquipmentSlot

STAT_LABELS = {
    "armor_class": "Armor Class",
    "attack_bonus": "Attack Bonus",
    "damage_bonus": "Damage Bonus",
    "strength": "Strength",
    "dexterity": "Dexterity",
    "constitution": "Constitution",
    "intelligence": "Intelligence",
    "wisdom": "Wisdom",
    "charisma": "Charisma",
    "walking_speed": "Walking Speed",
}

SLOT_POSITIONS = {
    EquipmentSlot.HEAD: (0, 0),
    EquipmentSlot.WAIST: (0, 2),
    EquipmentSlot.NECK: (1, 0),
    EquipmentSlot.LEGS: (1, 2),
    EquipmentSlot.CHEST: (2, 0),
    EquipmentSlot.FEET: (2, 2),
    EquipmentSlot.BACK: (3, 0),
    EquipmentSlot.RING_LEFT: (3, 2),
    EquipmentSlot.HANDS: (4, 0),
    EquipmentSlot.RING_RIGHT: (4, 2),
}
HAND_SLOTS = (EquipmentSlot.MAIN_HAND, EquipmentSlot.OFF_HAND)
SLOT_LABELS = {
    EquipmentSlot.RING_LEFT: "Ring 1",
    EquipmentSlot.RING_RIGHT: "Ring 2",
}


class EquipmentWidget:
    """Factory for the party leader equipment screen."""

    @staticmethod
    def create(
        app: Any,
        qt: Any,
        character_id: str,
        on_equip: Any = None,
        on_unequip: Any = None,
    ) -> Any:
        """Create a body outline, equipment slots, and gear-stat comparison."""
        character = app.characters.load(character_id)
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        title = qt.QtWidgets.QLabel(f"Equipment: {character.name}")
        layout.addWidget(title)

        body = qt.QtWidgets.QWidget()
        grid = qt.QtWidgets.QGridLayout(body)
        outline = qt.QtWidgets.QLabel("  O\n /|\\\n  |\n / \\")
        outline.setObjectName("EquipmentBodyOutline")
        if hasattr(outline, "setStyleSheet"):
            outline.setStyleSheet("font-size:30px; color:#d8dce8; padding:16px;")
        alignment = _alignment(qt, "AlignCenter")
        if alignment is not None and hasattr(outline, "setAlignment"):
            outline.setAlignment(alignment)
        grid.addWidget(outline, 0, 1, 5, 1)
        if hasattr(grid, "setColumnStretch"):
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(2, 1)

        equipped = {item.equipped_slot: item for item in character.inventory}
        for slot, (row, column) in SLOT_POSITIONS.items():
            button = _slot_button_for_character(
                app, qt, character, equipped, slot, on_equip, on_unequip
            )
            grid.addWidget(button, row, column)

        hand_row = qt.QtWidgets.QWidget()
        hand_layout = qt.QtWidgets.QHBoxLayout(hand_row)
        if hasattr(hand_layout, "addStretch"):
            hand_layout.addStretch(1)
        for slot in HAND_SLOTS:
            hand_layout.addWidget(
                _slot_button_for_character(
                    app, qt, character, equipped, slot, on_equip, on_unequip
                )
            )
        if hasattr(hand_layout, "addStretch"):
            hand_layout.addStretch(1)
        grid.addWidget(hand_row, 5, 0, 1, 3)
        layout.addWidget(body)
        layout.addWidget(_equipment_stats_table(app, qt, character))
        return widget


def _slot_button_for_character(
    app,
    qt,
    character,
    equipped,
    slot: EquipmentSlot,
    on_equip,
    on_unequip,
):
    """Create one equipment button with the character's compatible inventory."""
    return _equipment_slot_button(
        qt,
        slot,
        equipped.get(slot),
        app.inventory.compatible_items(character, slot),
        on_equip,
        on_unequip,
    )


def _equipment_slot_button(
    qt,
    slot: EquipmentSlot,
    item,
    compatible_items,
    on_equip,
    on_unequip,
):
    base_class = qt.QtWidgets.QPushButton

    class EquipmentDropSlot(base_class):
        def dragEnterEvent(self, event) -> None:  # noqa: N802
            if item_id_from_mime(event.mimeData()) is not None:
                event.acceptProposedAction()
                return
            event.ignore()

        def dropEvent(self, event) -> None:  # noqa: N802
            item_id = item_id_from_mime(event.mimeData())
            if item_id is not None and on_equip is not None:
                on_equip(item_id, slot)
                event.acceptProposedAction()

        def mousePressEvent(self, event) -> None:  # noqa: N802
            if _is_right_click(qt, event):
                _show_slot_menu(
                    qt,
                    self,
                    event,
                    slot,
                    item,
                    compatible_items,
                    on_equip,
                    on_unequip,
                )
                if hasattr(event, "accept"):
                    event.accept()
                return
            super().mousePressEvent(event)

    label = SLOT_LABELS.get(slot, slot.value.replace("_", " ").title())
    text = label if item is not None else f"{label}\nEmpty"
    button = EquipmentDropSlot(text)
    button.setObjectName(f"EquipmentSlot_{slot.value}")
    if hasattr(button, "setAcceptDrops"):
        button.setAcceptDrops(True)
    if hasattr(button, "setMinimumSize"):
        button.setMinimumSize(150, 58)
    if hasattr(button, "setToolTip"):
        detail = "Drop a compatible inventory item here or right-click to choose one."
        if item is not None:
            from dnd_combat_engine.gui import widgets

            detail = (
                f"{widgets._inventory_item_tooltip(item)}\n\n"
                "Right-click to replace or unequip it."
            )
        button.setToolTip(detail)
    if item is not None:
        _set_equipment_item_icon(qt, button, item)
        if hasattr(button, "setAccessibleName"):
            button.setAccessibleName(f"{label}: {item.name}")
    return button


def _set_equipment_item_icon(qt, button, item) -> None:
    """Display the inventory icon for an equipped item."""
    from dnd_combat_engine.gui import widgets

    icon_path = widgets._inventory_icon_path(item)
    icon_class = getattr(getattr(qt, "QtGui", None), "QIcon", None)
    if icon_path is None or icon_class is None or not hasattr(button, "setIcon"):
        return
    button.setIcon(icon_class(str(icon_path)))
    size_class = getattr(getattr(qt, "QtCore", None), "QSize", None)
    if size_class is not None and hasattr(button, "setIconSize"):
        button.setIconSize(size_class(40, 40))


def _show_slot_menu(
    qt,
    button,
    event,
    slot: EquipmentSlot,
    equipped_item,
    compatible_items,
    on_equip,
    on_unequip,
) -> None:
    menu_class = getattr(qt.QtWidgets, "QMenu", None)
    if menu_class is None:
        return
    menu = menu_class(button)
    for compatible in compatible_items:
        action = menu.addAction(f"Equip {compatible.name}")
        if hasattr(action, "setToolTip"):
            action.setToolTip(compatible.notes or compatible.name)
        if hasattr(action, "triggered") and on_equip is not None:
            action.triggered.connect(
                lambda checked=False, item_id=compatible.item_id: on_equip(item_id, slot)
            )
    if equipped_item is not None and on_unequip is not None:
        if compatible_items and hasattr(menu, "addSeparator"):
            menu.addSeparator()
        action = menu.addAction(f"Unequip {equipped_item.name}")
        if hasattr(action, "triggered"):
            action.triggered.connect(lambda checked=False: on_unequip(slot))
    if not compatible_items and equipped_item is None:
        action = menu.addAction("No compatible inventory items")
        if hasattr(action, "setEnabled"):
            action.setEnabled(False)
    position = _event_global_position(event)
    if hasattr(menu, "exec"):
        menu.exec(position)
    elif hasattr(menu, "exec_"):
        menu.exec_(position)


def _event_global_position(event):
    global_position = getattr(event, "globalPosition", None)
    if callable(global_position):
        point = global_position()
        return point.toPoint() if hasattr(point, "toPoint") else point
    global_pos = getattr(event, "globalPos", None)
    if callable(global_pos):
        return global_pos()
    position = getattr(event, "position", None)
    if callable(position):
        point = position()
        return point.toPoint() if hasattr(point, "toPoint") else point
    return None


def _equipment_stats_table(app, qt, character):
    stats = app.inventory.equipment_stats(character)
    table = qt.QtWidgets.QTableWidget(len(stats), 4)
    table.setObjectName("EquipmentStatsTable")
    table.setHorizontalHeaderLabels(("Statistic", "Base", "Gear", "Current"))
    for row, (name, (base, gear, current)) in enumerate(stats.items()):
        values = (STAT_LABELS.get(name, name.replace("_", " ").title()), base, gear, current)
        for column, value in enumerate(values):
            display = f"{value:+d}" if column == 2 and isinstance(value, int) else str(value)
            table.setItem(row, column, qt.QtWidgets.QTableWidgetItem(display))
    if hasattr(table, "resizeColumnsToContents"):
        table.resizeColumnsToContents()
    return table


def _alignment(qt, name: str):
    namespace = getattr(getattr(qt.QtCore, "Qt", None), "AlignmentFlag", None)
    return getattr(namespace, name, None) if namespace is not None else None


def _is_right_click(qt, event) -> bool:
    namespace = getattr(getattr(qt.QtCore, "Qt", None), "MouseButton", None)
    right = getattr(namespace, "RightButton", None) if namespace is not None else None
    return right is not None and event.button() == right
