"""PySide6 widgets for the desktop GUI."""

from __future__ import annotations

from dnd_combat_engine.app import DnDCombatEngineApp
from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.gui.editors import (
    add_character_to_campaign,
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

ACTION_BAR_HOTKEYS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=")


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


class CampaignEditorWidget:
    """Factory for campaign editing controls."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, campaign_id: str = "starter_campaign"):
        """Create a campaign editor widget."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        character_input = qt.QtWidgets.QLineEdit("vale")
        encounter_input = qt.QtWidgets.QLineEdit("roadside_ambush")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)

        _add_rows(output, campaign_reference_rows(app.campaigns.load(campaign_id)))

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
                lambda: add_character_to_campaign(app, campaign_id, character_input.text())
            )
        )
        remove_character = qt.QtWidgets.QPushButton("Remove Character")
        remove_character.clicked.connect(
            lambda: run(
                lambda: remove_character_from_campaign(app, campaign_id, character_input.text())
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
        layout.addWidget(add_character)
        layout.addWidget(remove_character)
        layout.addWidget(encounter_input)
        layout.addWidget(add_encounter)
        layout.addWidget(remove_encounter)
        layout.addWidget(output)
        return widget


class ActionBarWidget:
    """Factory for the bottom quick action bar."""

    @staticmethod
    def create(qt, session: ActionBarSession):
        """Create a centered action bar widget."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QHBoxLayout(widget)
        if hasattr(layout, "setAlignment"):
            layout.setAlignment(qt.QtCore.Qt.AlignmentFlag.AlignCenter)
        buttons = []
        for slot in range(1, 13):
            button = qt.QtWidgets.QPushButton("")
            if hasattr(button, "setFixedSize"):
                button.setFixedSize(86, 58)
            hotkey = ACTION_BAR_HOTKEYS[slot - 1]
            if hasattr(button, "setShortcut"):
                button.setShortcut(hotkey)
            button.clicked.connect(
                lambda checked=False, item_slot=slot: session.activate(item_slot)
            )
            buttons.append(button)
            layout.addWidget(button)

        def refresh(bar: ActionBar) -> None:
            for slot, button in enumerate(buttons, start=1):
                action = bar.button_at(slot)
                text = action.label if action else f"{ACTION_BAR_HOTKEYS[slot - 1]}\nEmpty"
                if hasattr(button, "setText"):
                    button.setText(text)
                if hasattr(button, "setEnabled"):
                    button.setEnabled(action is not None)
                if hasattr(button, "setToolTip"):
                    tooltip = "Empty action slot." if action is None else bar.activate(slot)
                    button.setToolTip(tooltip)

        session.subscribe(refresh)
        return widget


class SpellbookWidget:
    """Factory for the spellbook source window."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, session: ActionBarSession):
        """Create a spellbook widget that can place spells on the action bar."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        for spell_id in app.compendium.persistence_service.list_spell_ids():
            spell = app.compendium.load_spell(spell_id)
            button = qt.QtWidgets.QPushButton(f"{spell.name} (Rank {max(1, spell.level)})")
            button.clicked.connect(
                lambda checked=False, item=spell: output.append(
                    session.place_next(
                        ActionBarButton(
                            slot=1,
                            kind=ActionBarActionKind.SPELL,
                            action_id=item.spell_id,
                            name=item.name,
                            rank=max(1, item.level),
                            uses_highest_rank=True,
                        )
                    )
                )
            )
            layout.addWidget(button)
        layout.addWidget(output)
        return widget


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
        features = character.features or ("Basic Attack",)
        for feature in features:
            button = qt.QtWidgets.QPushButton(feature)
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


def _add_rows(output, rows: list[tuple[str, str]]) -> None:
    for field, value in rows:
        output.append(f"{field}: {value}")


def _add_participants(output, rows: list[tuple[str, str, str, str]]) -> None:
    for participant_id, name, kind, quantity in rows:
        output.append(f"{participant_id}: {name} ({kind}) x{quantity}")


def _action_id(name: str) -> str:
    return name.lower().replace(" ", "_").replace("'", "")
