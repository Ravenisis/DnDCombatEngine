"""Campaign, party, and target panel GUI components."""

from __future__ import annotations

from typing import Any, cast

from dnd_combat_engine.gui.editors import (
    add_encounter_to_campaign,
    remove_character_from_campaign,
    remove_encounter_from_campaign,
)
from dnd_combat_engine.gui.panels import campaign_reference_rows, campaign_rows
from dnd_combat_engine.models.effects import TargetKind, TargetReference
from dnd_combat_engine.models.encounters import ParticipantKind


class CampaignWidget:
    """Factory for the campaign workspace widget."""

    @staticmethod
    def create(app: Any, qt: Any, campaign_id: str = "starter_campaign") -> Any:
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
        app: Any,
        qt: Any,
        campaign_id: str = "starter_campaign",
        initiative_results: dict[str, int] | None = None,
        beacon_of_hope_targets: tuple[str, ...] = (),
        bless_targets: tuple[str, ...] = (),
        on_upload_sheet: Any = None,
        on_remove_member: Any = None,
        on_set_initiative: Any = None,
    ) -> Any:
        """Create party frames for every character in a campaign."""
        from dnd_combat_engine.gui import widgets

        campaign = app.campaigns.load(campaign_id)
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        if not campaign.character_ids:
            layout.addWidget(qt.QtWidgets.QLabel("No party members"))
            return widget
        for character_id in campaign.character_ids:
            layout.addWidget(
                widgets._party_member_frame(
                    app,
                    qt,
                    character_id,
                    initiative_results or {},
                    beacon_of_hope_targets,
                    bless_targets,
                    on_upload_sheet,
                    on_remove_member,
                    on_set_initiative,
                )
            )
        if hasattr(layout, "addStretch"):
            layout.addStretch(1)
        return widget


class TargetPanelWidget:
    """Factory for active target selection controls."""

    @staticmethod
    def create(
        app: Any,
        qt: Any,
        campaign_id: str | None,
        active_target: TargetReference | None = None,
        on_select: Any = None,
    ) -> Any:
        """Create a target selector for party and encounter participants."""
        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        active_text = "No target selected"
        if active_target is not None:
            active_text = f"Target: {active_target.name} ({active_target.kind.value})"
        layout.addWidget(qt.QtWidgets.QLabel(active_text))
        targets = _target_panel_references(app, campaign_id)
        if not targets:
            layout.addWidget(qt.QtWidgets.QLabel("No targets available"))
            return widget
        for target in targets:
            button = qt.QtWidgets.QPushButton(_target_button_text(app, target))
            if hasattr(button, "setToolTip"):
                button.setToolTip(f"Set active target to {target.name}")
            if (
                active_target is not None
                and target.target_id == active_target.target_id
                and hasattr(button, "setStyleSheet")
            ):
                button.setStyleSheet("border:2px solid #4f8cff; text-align:left;")
            button.clicked.connect(
                lambda checked=False, item=target: on_select(item)
                if on_select is not None
                else None
            )
            layout.addWidget(button)
        if hasattr(layout, "addStretch"):
            layout.addStretch(1)
        return widget


def _target_panel_references(app: Any, campaign_id: str | None) -> tuple[TargetReference, ...]:
    if campaign_id is None:
        return ()
    try:
        campaign = app.campaigns.load(campaign_id)
    except KeyError:
        return ()
    targets: list[TargetReference] = []
    for character_id in campaign.character_ids:
        try:
            character = app.characters.load(character_id)
        except KeyError:
            continue
        targets.append(
            TargetReference(
                target_id=character.character_id,
                name=character.name,
                kind=TargetKind.CHARACTER,
                source_id=character.character_id,
            )
        )
    for encounter_id in campaign.encounter_ids:
        try:
            encounter = app.encounters.load(encounter_id)
        except KeyError:
            continue
        for participant in encounter.participants:
            if participant.kind is ParticipantKind.MONSTER:
                targets.append(
                    TargetReference(
                        target_id=participant.participant_id,
                        name=participant.name,
                        kind=TargetKind.MONSTER,
                        source_id=participant.source_id,
                    )
                )
    return tuple(targets)


def _target_button_text(app: Any, target: TargetReference) -> str:
    if target.kind is TargetKind.CHARACTER:
        try:
            character = app.characters.load(target.source_id)
        except KeyError:
            return f"{target.name}\nMissing character"
        return (
            f"{character.name}\n"
            f"HP {character.hit_points.current}/{character.hit_points.maximum} "
            f"THP {character.hit_points.temporary}"
        )
    if target.kind is TargetKind.MONSTER:
        try:
            monster = app.compendium.load_monster(target.source_id)
        except KeyError:
            return f"{target.name}\nMissing monster"
        current_hp = _monster_target_current_hp(app, target, monster.hit_points.maximum)
        return f"{target.name}\nHP {current_hp}/{monster.hit_points.maximum}"
    return cast(str, target.name)


def _monster_target_current_hp(app: Any, target: TargetReference, default_hp: int) -> int:
    try:
        encounter_ids = app.encounters.persistence_service.list_encounter_ids()
    except AttributeError:
        return default_hp
    for encounter_id in encounter_ids:
        try:
            encounter = app.encounters.load(encounter_id)
        except KeyError:
            continue
        for participant in encounter.participants:
            if participant.participant_id == target.target_id:
                return int(participant.current_hit_points or default_hp * participant.quantity)
    return default_hp


class CampaignEditorWidget:
    """Factory for campaign editing controls."""

    @staticmethod
    def create(app: Any, qt: Any, campaign_id: str = "starter_campaign") -> Any:
        """Create a campaign editor widget."""
        from dnd_combat_engine.gui import widgets

        widget = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(widget)
        campaign = app.campaigns.load(campaign_id)
        character_input = _campaign_character_selector(qt, campaign.character_ids)
        encounter_input = qt.QtWidgets.QLineEdit("roadside_ambush")
        output = qt.QtWidgets.QTextEdit()
        output.setReadOnly(True)
        widgets._add_rows(output, campaign_reference_rows(campaign))

        def run(action: Any) -> None:
            try:
                message = action()
            except (ValueError, KeyError) as exc:
                message = str(exc)
            output.append(message)

        remove_character = qt.QtWidgets.QPushButton("Remove Character")
        remove_character.clicked.connect(
            lambda: run(
                lambda: remove_character_from_campaign(
                    app, campaign_id, _selector_text(character_input)
                )
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
        layout.addWidget(remove_character)
        layout.addWidget(encounter_input)
        layout.addWidget(add_encounter)
        layout.addWidget(remove_encounter)
        layout.addWidget(output)
        return widget


def _campaign_character_selector(qt: Any, character_ids: tuple[str, ...]) -> Any:
    combo_class = getattr(qt.QtWidgets, "QComboBox", None)
    if combo_class is None:
        return qt.QtWidgets.QLineEdit(character_ids[0] if character_ids else "")
    combo = combo_class()
    for character_id in character_ids:
        combo.addItem(character_id)
    return combo


def _selector_text(widget: Any) -> str:
    if hasattr(widget, "currentText"):
        return str(widget.currentText()).strip()
    if hasattr(widget, "text"):
        return str(widget.text()).strip()
    return ""
