import pytest

from dnd_combat_engine.models import Condition, ConditionName


def test_condition_round_trip_to_plain_data() -> None:
    condition = Condition(
        name=ConditionName.POISONED,
        source="Giant Spider",
        remaining_rounds=3,
    )

    restored = Condition.from_dict(condition.to_dict())

    assert restored == condition


def test_condition_ticks_down_and_expires() -> None:
    condition = Condition(ConditionName.STUNNED, remaining_rounds=2)

    ticked = condition.tick_round()

    assert ticked == Condition(ConditionName.STUNNED, remaining_rounds=1)
    assert ticked.tick_round() is None


def test_condition_without_duration_does_not_expire() -> None:
    condition = Condition(ConditionName.PRONE)

    assert condition.tick_round() is condition


def test_condition_rejects_invalid_duration() -> None:
    with pytest.raises(ValueError):
        Condition(ConditionName.BLINDED, remaining_rounds=0)

