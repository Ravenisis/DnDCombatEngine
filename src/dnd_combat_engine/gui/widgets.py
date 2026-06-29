"""PySide6 widgets for the desktop GUI."""

from __future__ import annotations

from dnd_combat_engine.app import DnDCombatEngineApp
from dnd_combat_engine.gui.panels import (
    attack_summary_text,
    campaign_rows,
    character_sheet_rows,
    encounter_rows,
    initiative_rows,
)
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
    def create(app: DnDCombatEngineApp, qt):
        """Create a quick attack widget backed by controllers."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        button = qt.QtWidgets.QPushButton("Quick Attack")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)

        def attack() -> None:
            attacker = app.characters.load("vale")
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
                active_features=("Sneak Attack",),
            )
            output.append(attack_summary_text(result))

        button.clicked.connect(attack)
        layout.addWidget(button)
        layout.addWidget(output)
        return widget
