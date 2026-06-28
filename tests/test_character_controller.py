from dnd_combat_engine.controllers import CharacterController
from dnd_combat_engine.models import Character, Condition, ConditionName, HitPoints, ResourcePool
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import CharacterService, PersistenceService


def make_controller(tmp_path) -> CharacterController:
    return CharacterController(
        character_service=CharacterService(),
        persistence_service=PersistenceService(JsonFileStore(tmp_path)),
    )


def test_character_controller_applies_damage_and_autosaves(tmp_path) -> None:
    controller = make_controller(tmp_path)
    character = Character("cleric", "Mira", HitPoints(10, 10))
    controller.save(character)

    applied = controller.apply_damage(character, 4, autosave=True)
    restored = controller.load("cleric")

    assert applied == 4
    assert restored.hit_points.current == 6


def test_character_controller_manages_conditions_and_resources(tmp_path) -> None:
    controller = make_controller(tmp_path)
    character = Character("monk", "Tavi", HitPoints(9, 9))

    controller.add_condition(character, Condition(ConditionName.PRONE))
    controller.set_resource(character, ResourcePool("ki", current=2, maximum=2))

    assert character.conditions == (Condition(ConditionName.PRONE),)
    assert character.resources["ki"].current == 2
    assert controller.remove_condition(character, ConditionName.PRONE) is True
    assert controller.heal(character, 10) == 0

