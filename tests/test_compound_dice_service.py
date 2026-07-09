from dnd_combat_engine.services import DiceService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def test_dice_service_rolls_compound_spell_damage() -> None:
    result = DiceService().roll("2d8+4d6", rng=SequenceRng([5, 6, 1, 2, 3, 4]))

    assert result.total == 21
    assert result.rolls == (5, 6, 1, 2, 3, 4)


def test_dice_service_rolls_signed_compound_terms() -> None:
    result = DiceService().roll("2d8-1d6+3", rng=SequenceRng([5, 6, 4]))

    assert result.total == 10
    assert result.rolls == (5, 6, -4)
    assert result.modifier == 3


def test_dice_service_treats_spellcasting_modifier_placeholder_as_zero() -> None:
    result = DiceService().roll("1d8+spellcasting_modifier", rng=SequenceRng([7]))

    assert result.total == 7
    assert result.notation == "1d8"


def test_dice_service_accepts_flat_srd_damage_values() -> None:
    result = DiceService().roll("60")

    assert result.total == 60
    assert result.modifier == 60


def test_dice_service_averages_compound_and_flat_values() -> None:
    service = DiceService()

    assert service.average("2d8+4d6") == 23
    assert service.average("60") == 60
    assert service.average("1d8 + spellcasting_modifier") == 4.5


def test_dice_service_rejects_invalid_compound_notation() -> None:
    try:
        DiceService().roll("2d8++4")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    try:
        DiceService().average("2d8++4")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
