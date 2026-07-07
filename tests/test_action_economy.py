import pytest

from dnd_combat_engine.models import ActionCost, TurnEconomy


def test_turn_economy_spends_actions_and_resets_turn() -> None:
    economy = TurnEconomy(movement_maximum=30)

    assert economy.spend(ActionCost.ACTION) is True
    assert economy.spend(ActionCost.ACTION) is False
    assert economy.spend(ActionCost.BONUS_ACTION) is True
    assert economy.spend(ActionCost.MOVEMENT, 20) is True
    assert economy.spend(ActionCost.MOVEMENT, 15) is False

    economy.reset_turn()

    assert economy.action_used is False
    assert economy.bonus_action_used is False
    assert economy.movement_spent == 0


def test_turn_economy_tracks_reactions_separately() -> None:
    economy = TurnEconomy()

    assert economy.spend(ActionCost.REACTION) is True
    assert economy.spend(ActionCost.REACTION) is False
    economy.reset_turn()
    assert economy.reaction_used is True
    economy.reset_reaction()
    assert economy.reaction_used is False


def test_turn_economy_round_trips_to_plain_data() -> None:
    economy = TurnEconomy(action_used=True, movement_spent=10, movement_maximum=25)

    assert TurnEconomy.from_dict(economy.to_dict()) == economy


def test_turn_economy_rejects_invalid_movement() -> None:
    with pytest.raises(ValueError):
        TurnEconomy(movement_maximum=-1)
    with pytest.raises(ValueError):
        TurnEconomy(movement_spent=-1)
    with pytest.raises(ValueError):
        TurnEconomy(movement_spent=40, movement_maximum=30)
    with pytest.raises(ValueError):
        TurnEconomy().can_spend(ActionCost.MOVEMENT, -1)

