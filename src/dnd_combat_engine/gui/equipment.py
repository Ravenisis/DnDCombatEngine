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
    EquipmentSlot.HEAD: (0, 1),
    EquipmentSlot.NECK: (1, 0),
    EquipmentSlot.BACK: (1, 2),
    EquipmentSlot.CHEST: (2, 1),
    EquipmentSlot.MAIN_HAND: (3, 0),
    EquipmentSlot.OFF_HAND: (3, 2),
    EquipmentSlot.HANDS: (4, 0),
    EquipmentSlot.WAIST: (4, 2),
    EquipmentSlot.LEGS: (5, 1),
    EquipmentSlot.RING_LEFT: (5, 0),
    EquipmentSlot.RING_RIGHT: (5, 2),
    EquipmentSlot.FEET: (6, 1),
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
        grid.addWidget(outline, 1, 1, 5, 1)

        equipped = {item.equipped_slot: item for item in character.inventory}
        for slot, (row, column) in SLOT_POSITIONS.items():
            item = equipped.get(slot)
            compatible_items = app.inventory.compatible_items(character, slot)
            button = _equipment_slot_button(
                qt,
                slot,
                item,
                compatible_items,
                on_equip,
                on_unequip,
            )
            grid.addWidget(button, row, column)
        layout.addWidget(body)
        layout.addWidget(_equipment_stats_table(app, qt, character))
        return widget


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

    label = slot.value.replace("_", " ").title()
    text = f"{label}\n{item.name if item is not None else 'Empty'}"
    button = EquipmentDropSlot(text)
    button.setObjectName(f"EquipmentSlot_{slot.value}")
    if hasattr(button, "setAcceptDrops"):
        button.setAcceptDrops(True)
    if hasattr(button, "setMinimumSize"):
        button.setMinimumSize(150, 58)
    if hasattr(button, "setToolTip"):
        detail = "Drop a compatible inventory item here or right-click to choose one."
        if item is not None:
            detail = f"{item.name}\nRight-click to replace or unequip it."
        button.setToolTip(detail)
    return button


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
