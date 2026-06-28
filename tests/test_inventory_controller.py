from dnd_combat_engine.controllers import InventoryController
from dnd_combat_engine.models import Character, HitPoints, InventoryItem
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import InventoryService, PersistenceService


def make_controller(tmp_path) -> InventoryController:
    return InventoryController(
        inventory_service=InventoryService(),
        persistence_service=PersistenceService(JsonFileStore(tmp_path)),
    )


def test_inventory_controller_adds_removes_and_autosaves_items(tmp_path) -> None:
    controller = make_controller(tmp_path)
    character = Character("rogue", "Vale", HitPoints(10, 10))
    controller.persistence_service.save_character(character)

    controller.add_item(
        character,
        InventoryItem("torch", "Torch", quantity=3, weight=1.0),
        autosave=True,
    )
    removed = controller.remove_item(character, "torch", quantity=2, autosave=True)
    restored = controller.persistence_service.load_character("rogue")

    assert removed is True
    assert restored.inventory[0].quantity == 1
    assert controller.carried_weight(restored) == 1.0

