"""Combat-oriented widget factories kept separate from general GUI widgets."""

from __future__ import annotations

from typing import Any

from dnd_combat_engine.app import DnDCombatEngineApp
from dnd_combat_engine.gui.editors import (
    add_character_to_encounter,
    add_monster_to_encounter,
    advance_encounter_round,
    complete_encounter,
    remove_participant_from_encounter,
    start_encounter,
)
from dnd_combat_engine.gui.panels import (
    attack_summary_text,
    character_sheet_rows,
    encounter_participant_rows,
    encounter_rows,
    initiative_rows,
)
from dnd_combat_engine.models import CombatLog


class DiceTrayWidget:
    """Factory for the dice tray widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt: Any) -> Any:
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
    def create(qt: Any, log: CombatLog | None = None) -> Any:
        """Create a combat log widget."""
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        for entry in (log or CombatLog()).entries:
            output.append(entry.message)
        return output


class CampaignActivityWidget:
    """Factory for persisted campaign activity rows."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt: Any, campaign_id: str | None = None) -> Any:
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
        for entry in campaign.activity_log:
            output.append(f"[{entry.category}] {entry.message}")
        return output


class CharacterSheetWidget:
    """Factory for the character sheet widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt: Any, character_id: str = "vale") -> Any:
        """Create a compact character sheet widget."""
        character = app.characters.load(character_id)
        rows = character_sheet_rows(character)
        table = qt.QtWidgets.QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Field", "Value"])
        for row, (field, value) in enumerate(rows):
            table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(field))
            table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(value))
        return table


class EncounterTrackerWidget:
    """Factory for the encounter tracker widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt: Any, encounter_id: str = "roadside_ambush") -> Any:
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
    def create(app: DnDCombatEngineApp, qt: Any, encounter_id: str = "roadside_ambush") -> Any:
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

        def run(action: Any) -> None:
            try:
                message = action()
            except (KeyError, ValueError) as exc:
                message = str(exc)
            output.append(message)

        for label, callback in (
            (
                "Add Character",
                lambda: add_character_to_encounter(app, encounter_id, character_input.text()),
            ),
            (
                "Add Monster",
                lambda: add_monster_to_encounter(
                    app, encounter_id, monster_input.text(), int(quantity_input.text())
                ),
            ),
            (
                "Remove Participant",
                lambda: remove_participant_from_encounter(
                    app, encounter_id, participant_input.text()
                ),
            ),
            ("Start", lambda: start_encounter(app, encounter_id)),
            ("Advance Round", lambda: advance_encounter_round(app, encounter_id)),
            ("Complete", lambda: complete_encounter(app, encounter_id)),
        ):
            button = qt.QtWidgets.QPushButton(label)
            button.clicked.connect(lambda checked=False, item=callback: run(item))
            if label == "Add Character":
                layout.addWidget(character_input)
            elif label == "Add Monster":
                layout.addWidget(monster_input)
                layout.addWidget(quantity_input)
            elif label == "Remove Participant":
                layout.addWidget(participant_input)
            layout.addWidget(button)
        layout.addWidget(output)
        return widget


class InitiativeWidget:
    """Factory for the initiative widget."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt: Any, character_id: str = "vale") -> Any:
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
        qt: Any,
        character_id: str | None = None,
        campaign_id: str = "starter_campaign",
    ) -> Any:
        """Create a quick attack widget backed by controllers."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        button = qt.QtWidgets.QPushButton("Quick Attack")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        button.clicked.connect(
            lambda: output.append(_quick_attack_message(app, character_id, campaign_id))
        )
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
    names = {
        part.strip().lower()
        for feature in features
        for part in feature.split(",")
        if part.strip()
    }
    supported = ("Sneak Attack", "Bless", "Rage", "Hex")
    return tuple(feature for feature in supported if feature.lower() in names)


def _add_participants(output: Any, rows: list[tuple[str, str, str, str]]) -> None:
    for participant_id, name, kind, quantity in rows:
        output.append(f"{participant_id}: {name} ({kind}) x{quantity}")
