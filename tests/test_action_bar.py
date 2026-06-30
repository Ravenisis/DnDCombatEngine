import pytest

from dnd_combat_engine.gui.action_bar import ActionBarSession
from dnd_combat_engine.models import ActionBar, ActionBarActionKind, ActionBarButton


def test_action_bar_places_and_activates_buttons() -> None:
    bar = ActionBar(slot_count=2).place(
        ActionBarButton(
            slot=1,
            kind=ActionBarActionKind.SPELL,
            action_id="fireball",
            name="Fireball",
            rank=3,
            hotkey="1",
        )
    )

    assert bar.button_at(1) is not None
    assert bar.next_open_slot() == 2
    assert bar.activate(1) == "Activated Fireball rank 3."
    assert bar.activate(2) == "Slot 2 is empty."
    assert bar.button_at(1).label == "1\nFireball R3"  # type: ignore[union-attr]


def test_action_bar_updates_only_highest_rank_active_spec_buttons() -> None:
    bar = ActionBar(
        buttons=(
            ActionBarButton(1, ActionBarActionKind.SPELL, "heal", "Heal", rank=2),
            ActionBarButton(
                2,
                ActionBarActionKind.SPELL,
                "heal",
                "Heal",
                rank=1,
                uses_highest_rank=False,
            ),
            ActionBarButton(
                3,
                ActionBarActionKind.SPELL,
                "heal",
                "Heal",
                rank=2,
                active_spec=False,
            ),
        )
    )

    updated = bar.with_learned_rank("heal", 3)

    assert updated.button_at(1).rank == 3  # type: ignore[union-attr]
    assert updated.button_at(2).rank == 1  # type: ignore[union-attr]
    assert updated.button_at(3).rank == 2  # type: ignore[union-attr]


def test_action_bar_rejects_duplicate_slots() -> None:
    with pytest.raises(ValueError):
        ActionBar(
            buttons=(
                ActionBarButton(1, ActionBarActionKind.ABILITY, "a", "A"),
                ActionBarButton(1, ActionBarActionKind.ABILITY, "b", "B"),
            )
        )


def test_action_bar_session_places_next_and_notifies() -> None:
    session = ActionBarSession(ActionBar(slot_count=2))
    seen = []
    session.subscribe(seen.append)

    assert session.place_next(
        ActionBarButton(
            slot=1,
            kind=ActionBarActionKind.ABILITY,
            action_id="sneak_attack",
            name="Sneak Attack",
        )
    ) == "Placed Sneak Attack on slot 1."
    assert session.learn_rank("sneak_attack", 2) == "Learned rank 2 for sneak_attack."

    assert len(seen) == 3
    assert session.bar.button_at(1).rank == 2  # type: ignore[union-attr]

