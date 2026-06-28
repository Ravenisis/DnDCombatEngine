from dnd_combat_engine.models import Character, HitPoints
from dnd_combat_engine.services import CharacterService, DiceService


def test_character_service_applies_damage_and_healing() -> None:
    character = Character(
        character_id="cleric-1",
        name="Mira",
        hit_points=HitPoints(current=4, maximum=10),
    )
    service = CharacterService()

    assert service.apply_damage(character, 3) == 3
    assert character.hit_points.current == 1
    assert service.heal(character, 20) == 9
    assert character.hit_points.current == 10


def test_dice_service_reports_average() -> None:
    assert DiceService().average("d20") == 10.5

