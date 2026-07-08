"""End-to-end GUI smoke coverage for action-bar combat workflows."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from dnd_combat_engine.app import create_app
from dnd_combat_engine.gui import main_window
from dnd_combat_engine.models import (
    ActionBarActionKind,
    ActionBarButton,
    TargetKind,
    TargetReference,
)
from dnd_combat_engine.utils.paths import initialize_user_data

pytestmark = pytest.mark.gui

if os.environ.get("DND_COMBAT_ENGINE_GUI_SMOKE") != "1":
    pytest.skip(
        "Set DND_COMBAT_ENGINE_GUI_SMOKE=1 to run PySide6 GUI smoke tests.",
        allow_module_level=True,
    )

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6")


@pytest.fixture()
def gui_workspace(tmp_path: Path, qtbot):
    """Create an isolated GUI workspace with writable seed data."""
    app = create_app(initialize_user_data(tmp_path / "data"))
    window = main_window.create_main_window(app)
    qtbot.addWidget(window)
    window.show()

    state = window._dnd_campaign_state  # noqa: SLF001
    state.active_campaign_id = "starter_campaign"
    state.selected_character_id = "ravenisis"
    state.party_leader_character_id = "ravenisis"
    return app, window, state


def test_action_bar_target_attack_updates_workspace_and_monster_hp(gui_workspace, qtbot) -> None:
    """Clicking a slotted attack should resolve against the active monster target."""
    app, window, state = gui_workspace
    state.active_target = TargetReference(
        target_id="goblin",
        name="Goblin",
        kind=TargetKind.MONSTER,
        source_id="goblin",
    )
    session = window._dnd_action_bar_session  # noqa: SLF001
    session.place(
        ActionBarButton(
            slot=1,
            kind=ActionBarActionKind.ABILITY,
            action_id="unarmed_strike",
            name="Unarmed Strike",
        )
    )

    starting_hp = _monster_hit_points(app, "goblin")
    qt = main_window.load_qt()
    qtbot.mouseClick(_button_with_text(window, qt, "Unarmed Strike"), _left_button(qt))
    qtbot.waitUntil(
        lambda: "Unarmed Strike" in _workspace_text(window),
        timeout=3_000,
    )

    assert _monster_hit_points(app, "goblin") < starting_hp
    assert "Applied" in _workspace_text(window)
    assert _campaign_has_activity(app, "starter_campaign", "action", "Unarmed Strike")


def test_action_bar_concentration_spell_persists_and_cleans_up(
    gui_workspace,
    qtbot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clicking a concentration spell should persist buffs and cleanup on break."""
    app, window, state = gui_workspace
    monkeypatch.setattr(
        main_window,
        "_choose_party_targets",
        lambda *args, **kwargs: ("ravenisis", "bran"),
    )
    session = window._dnd_action_bar_session  # noqa: SLF001
    session.place(
        ActionBarButton(
            slot=1,
            kind=ActionBarActionKind.SPELL,
            action_id="bless",
            name="Bless",
        )
    )

    qt = main_window.load_qt()
    qtbot.mouseClick(_button_with_text(window, qt, "Bless"), _left_button(qt))
    qtbot.waitUntil(lambda: state.active_concentration is not None, timeout=3_000)

    assert state.concentration_spell_id == "bless"
    assert set(state.bless_targets) == {"ravenisis", "bran"}
    campaign = app.campaigns.load("starter_campaign")
    assert campaign.active_concentration is not None
    assert campaign.active_concentration.effect_id == "bless"
    assert {target.target_id for target in campaign.active_concentration.targets} == {
        "ravenisis",
        "bran",
    }

    main_window._break_concentration_from_menu(window, qt, app, state)  # noqa: SLF001
    qtbot.waitUntil(lambda: state.active_concentration is None, timeout=3_000)

    assert state.bless_targets == ()
    assert app.campaigns.load("starter_campaign").active_concentration is None
    assert "Concentration broken" in _workspace_text(window)
    assert _campaign_has_activity(app, "starter_campaign", "concentration", "Bless")


def _left_button(qt):
    button_namespace = getattr(qt.QtCore.Qt, "MouseButton", qt.QtCore.Qt)
    return button_namespace.LeftButton


def _button_with_text(window, qt, expected_text: str):
    buttons = window.findChildren(qt.QtWidgets.QPushButton)
    for button in buttons:
        if expected_text in button.text():
            return button
    available = ", ".join(button.text().replace("\n", " ") for button in buttons)
    raise AssertionError(f"Could not find button containing {expected_text!r}. Buttons: {available}")


def _workspace_text(window) -> str:
    workspace = window._dnd_central  # noqa: SLF001
    return workspace.toPlainText() if hasattr(workspace, "toPlainText") else str(workspace)


def _monster_hit_points(app, participant_id: str) -> int:
    encounter = app.encounters.load("roadside_ambush")
    participant = next(
        item for item in encounter.participants if item.participant_id == participant_id
    )
    monster = app.compendium.load_monster(participant.source_id)
    return participant.current_hit_points or monster.hit_points.maximum * participant.quantity


def _campaign_has_activity(app, campaign_id: str, category: str, text: str) -> bool:
    campaign = app.campaigns.load(campaign_id)
    return any(
        entry.category == category and text in entry.message for entry in campaign.activity_log
    )
