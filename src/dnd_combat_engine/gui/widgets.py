"""PySide6 widgets for the desktop GUI."""

from __future__ import annotations

import re
import textwrap

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


class PartyFramesWidget:
    """Factory for framed party member summaries."""

    @staticmethod
    def create(
        app: DnDCombatEngineApp,
        qt,
        campaign_id: str = "starter_campaign",
        initiative_results: dict[str, int] | None = None,
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
                    on_upload_sheet,
                    on_remove_member,
                    on_set_initiative,
                )
            )
        if hasattr(layout, "addStretch"):
            layout.addStretch(1)
        return widget


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
    def create(qt, session: ActionBarSession, on_activate=None):
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
                    tooltip = (
                        "Empty action slot."
                        if action is None
                        else f"{bar.activate(slot)} Shift+right-click to remove."
                    )
                    button.setToolTip(tooltip)

        session.subscribe(refresh)
        return widget


class SpellSlotTrackerWidget:
    """Factory for compact spell slot tracking next to the action bar."""

    @staticmethod
    def create(app: DnDCombatEngineApp, qt, character_id: str | None = None):
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
        slot_rows = _spell_slot_rows(character.resources)
        if not slot_rows:
            layout.addWidget(qt.QtWidgets.QLabel("None"))
            return widget
        for level, current, maximum in slot_rows:
            layout.addWidget(qt.QtWidgets.QLabel(f"L{level}: {current}/{maximum}"))
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
        for spell_id in _spell_ids_for_character(app, character_id):
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


def _spell_slot_rows(resources) -> tuple[tuple[int, int, int], ...]:
    rows = []
    for name, resource in resources.items():
        match = re.fullmatch(r"spell_slot_(\d+)", name)
        if match:
            rows.append((int(match.group(1)), resource.current, resource.maximum))
    return tuple(sorted(rows))


def _action_button_text(hotkey: str, action: ActionBarButton | None) -> str:
    """Return wrapped action bar text with the shortcut on the first line."""
    if action is None:
        return f"{hotkey}\nEmpty"
    rank = f" R{action.rank}" if action.rank > 1 else ""
    return f"{hotkey}\n{_wrap_action_label(f'{action.name}{rank}')}"


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

    layout.addWidget(qt.QtWidgets.QLabel(f"{character.name}"))
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
    features = ", ".join(character.features) if character.features else "No features"
    layout.addWidget(qt.QtWidgets.QLabel(features))
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
    _add_menu_action(menu, "Upload New Character Sheet", on_upload_sheet, character_id)
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
