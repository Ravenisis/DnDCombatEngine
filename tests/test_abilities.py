import pytest

from dnd_combat_engine.models import AbilityScores


def test_ability_modifier_uses_dnd_formula() -> None:
    abilities = AbilityScores(strength=8, dexterity=14, constitution=20)

    assert abilities.modifier("strength") == -1
    assert abilities.modifier("dexterity") == 2
    assert abilities.modifier("constitution") == 5


def test_ability_scores_must_be_positive() -> None:
    with pytest.raises(ValueError):
        AbilityScores(strength=0)

