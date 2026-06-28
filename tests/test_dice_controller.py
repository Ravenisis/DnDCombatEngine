import random

from dnd_combat_engine.controllers import DiceController
from dnd_combat_engine.services import DiceService


def test_dice_controller_rolls_dice() -> None:
    result = DiceController(DiceService()).roll("1d6+2", rng=random.Random(1))

    assert result.total == 4


def test_dice_controller_describes_notation() -> None:
    description = DiceController(DiceService()).describe("4d6dl1")

    assert description == {
        "notation": "4d6dl1",
        "minimum": 3,
        "maximum": 18,
        "average": 12.244598765432098,
    }

