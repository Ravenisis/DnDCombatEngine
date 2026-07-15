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
            button = _equipment_slot_button(qt, slot, item, on_equip, on_unequip)
            grid.addWidget(button, row, column)
        layout.addWidget(body)
        layout.addWidget(_equipment_stats_table(app, qt, character))
        return widget


def _equipment_slot_button(qt, slot: EquipmentSlot, item, on_equip, on_unequip):
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
            if item is not None and _is_right_click(qt, event) and on_unequip is not None:
                on_unequip(slot)
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
        detail = "Drop a compatible inventory item here."
        if item is not None:
            detail = f"{item.name}\nRight-click to unequip."
        button.setToolTip(detail)
    return button


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
