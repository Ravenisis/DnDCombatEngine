"""PySide6 widgets for the desktop GUI."""

from __future__ import annotations

from dnd_combat_engine.app import DnDCombatEngineApp
from dnd_combat_engine.models import CombatLog


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


class CharacterSheetWidget:
    """Factory for the character sheet widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, character_id: str = "vale"):
        """Create a compact character sheet widget."""
        character = app.characters.load(character_id)
        table = qt.QtWidgets.QTableWidget(4, 2)
        table.setHorizontalHeaderLabels(["Field", "Value"])
        rows = [
            ("Name", character.name),
            ("HP", f"{character.hit_points.current}/{character.hit_points.maximum}"),
            ("Level", str(character.level)),
            ("Features", ", ".join(character.features)),
        ]
        for row, (field, value) in enumerate(rows):
            table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(field))
            table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(value))
        return table

