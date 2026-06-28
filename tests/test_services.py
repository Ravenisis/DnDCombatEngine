from dnd_combat_engine.models import Character, Condition, ConditionName, HitPoints, ResourcePool
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


def test_character_service_manages_conditions() -> None:
    character = Character(
        character_id="fighter-1",
        name="Bran",
        hit_points=HitPoints(current=12, maximum=12),
    )
    service = CharacterService()

    service.add_condition(character, Condition(ConditionName.POISONED, remaining_rounds=2))
    service.add_condition(character, Condition(ConditionName.POISONED, remaining_rounds=2))

    assert service.has_condition(character, ConditionName.POISONED) is True
    assert len(character.conditions) == 1
    service.tick_conditions(character)
    assert character.conditions[0].remaining_rounds == 1
    service.tick_conditions(character)
    assert service.has_condition(character, ConditionName.POISONED) is False


def test_character_service_removes_conditions_and_manages_resources() -> None:
    character = Character(
        character_id="monk-1",
        name="Tavi",
        hit_points=HitPoints(current=9, maximum=9),
    )
    service = CharacterService()

    service.add_condition(character, Condition(ConditionName.PRONE))
    service.set_resource(character, ResourcePool("ki", current=2, maximum=2))

    assert service.remove_condition(character, ConditionName.PRONE) is True
    assert service.remove_condition(character, ConditionName.PRONE) is False
    assert service.expend_resource(character, "ki") is True
    assert service.expend_resource(character, "missing") is False
    assert service.restore_resource(character, "ki", 10) == 1
    assert service.restore_resource(character, "missing", 10) == 0


def test_dice_service_reports_average() -> None:
    assert DiceService().average("d20") == 10.5
