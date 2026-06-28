import pytest

from dnd_combat_engine.engine import InitiativeEntry, InitiativeTracker
from dnd_combat_engine.models import AbilityScores, Character, HitPoints
from dnd_combat_engine.services import InitiativeService
from dnd_combat_engine.utils import DiceRollResult


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def make_character(
    character_id: str,
    name: str,
    dexterity: int = 10,
) -> Character:
    return Character(
        character_id=character_id,
        name=name,
        hit_points=HitPoints(10, 10),
        abilities=AbilityScores(dexterity=dexterity),
    )


def make_entry(character: Character, total: int) -> InitiativeEntry:
    return InitiativeEntry(
        combatant=character,
        roll=DiceRollResult("1d20", total, (total,), (total,)),
        dexterity_modifier=character.abilities.modifier("dexterity"),
        total=total,
    )


def test_initiative_service_sorts_by_total_then_dexterity_then_name() -> None:
    rogue = make_character("rogue", "Vale", dexterity=16)
    fighter = make_character("fighter", "Bran", dexterity=10)
    wizard = make_character("wizard", "Aria", dexterity=14)

    tracker = InitiativeService().roll_initiative(
        [fighter, wizard, rogue],
        rng=SequenceRng([14, 12, 11]),  # type: ignore[arg-type]
    )

    assert [entry.combatant.character_id for entry in tracker.entries] == [
        "rogue",
        "wizard",
        "fighter",
    ]
    assert tracker.current is tracker.entries[0]
    assert {entry.total for entry in tracker.entries} == {14}


def test_initiative_tracker_advances_turns_and_rounds() -> None:
    first = make_entry(make_character("first", "First"), 20)
    second = make_entry(make_character("second", "Second"), 10)
    tracker = InitiativeTracker((first, second))

    second_turn = tracker.advance()
    next_round = second_turn.advance()

    assert second_turn.current is second
    assert second_turn.round_number == 1
    assert next_round.current is first
    assert next_round.round_number == 2


def test_initiative_tracker_handles_empty_order() -> None:
    tracker = InitiativeTracker(())

    assert tracker.current is None
    assert tracker.advance() is tracker
    assert tracker.ordered_combatants == ()


def test_initiative_tracker_removes_current_and_previous_combatants() -> None:
    first = make_entry(make_character("first", "First"), 20)
    second = make_entry(make_character("second", "Second"), 10)
    third = make_entry(make_character("third", "Third"), 5)
    tracker = InitiativeTracker((first, second, third), active_index=1)

    without_current = tracker.remove("second")
    without_previous = tracker.remove("first")

    assert [entry.combatant.character_id for entry in without_current.entries] == [
        "first",
        "third",
    ]
    assert without_current.current is third
    assert without_previous.current is second


def test_initiative_tracker_remove_unknown_combatant_returns_same_tracker() -> None:
    first = make_entry(make_character("first", "First"), 20)
    tracker = InitiativeTracker((first,))

    assert tracker.remove("missing") is tracker


def test_initiative_tracker_remove_last_combatant_returns_empty_tracker() -> None:
    first = make_entry(make_character("first", "First"), 20)
    tracker = InitiativeTracker((first,))

    empty = tracker.remove("first")

    assert empty.entries == ()
    assert empty.current is None


def test_initiative_tracker_validates_bounds() -> None:
    entry = make_entry(make_character("first", "First"), 20)

    with pytest.raises(ValueError):
        InitiativeTracker((entry,), active_index=1)
    with pytest.raises(ValueError):
        InitiativeTracker((), active_index=1)
    with pytest.raises(ValueError):
        InitiativeTracker((entry,), round_number=0)


def test_initiative_service_requires_combatants() -> None:
    with pytest.raises(ValueError):
        InitiativeService().roll_initiative([])
