import random

import pytest

from dnd_combat_engine.services import DiceService
from dnd_combat_engine.utils import DiceExpression


def test_parse_basic_dice_notation() -> None:
    expression = DiceExpression.parse("2d6+5")

    assert expression.count == 2
    assert expression.sides == 6
    assert expression.modifier == 5
    assert expression.minimum() == 7
    assert expression.maximum() == 17
    assert expression.average() == 12


def test_single_die_defaults_to_one_die() -> None:
    expression = DiceExpression.parse("d20")

    assert expression.count == 1
    assert expression.notation == "1d20"


def test_parse_keep_highest_and_keep_lowest() -> None:
    assert DiceExpression.parse("4d8kh3").keep_highest == 3
    assert DiceExpression.parse("3d20kl1").keep_lowest == 1


def test_keep_lowest_changes_minimum_and_maximum() -> None:
    expression = DiceExpression.parse("3d20kl1")

    assert expression.minimum() == 1
    assert expression.maximum() == 20


def test_roll_is_deterministic_with_seeded_rng() -> None:
    result = DiceService().roll("2d6+1", rng=random.Random(2))

    assert result.rolls == (1, 1)
    assert result.kept == (1, 1)
    assert result.total == 3


def test_exploding_dice_have_no_finite_maximum() -> None:
    expression = DiceExpression.parse("1d6!")

    assert expression.maximum() is None
    assert expression.minimum() == 1


def test_reroll_low_values_changes_average() -> None:
    expression = DiceExpression.parse("1d6r1")

    assert expression.reroll_threshold == 1
    assert expression.average() == pytest.approx(23.5 / 6)


def test_unsupported_high_reroll_raises_value_error() -> None:
    with pytest.raises(ValueError):
        DiceExpression.parse("1d6r>3")


def test_invalid_notation_raises_value_error() -> None:
    with pytest.raises(ValueError):
        DiceExpression.parse("not dice")
