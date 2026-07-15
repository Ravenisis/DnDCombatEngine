from dnd_combat_engine.controllers import InventoryController
from dnd_combat_engine.models import (
    Character,
    EquipmentSlot,
    HitPoints,
    InventoryItem,
    ItemCategory,
)
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


def test_inventory_controller_moves_and_equips_with_autosave(tmp_path) -> None:
    controller = make_controller(tmp_path)
    character = Character(
        "fighter",
        "Fighter",
        HitPoints(20, 20),
        inventory=(
            InventoryItem("backpack", "Backpack", tags=("container",)),
            InventoryItem("longsword", "Longsword", category=ItemCategory.WEAPON),
        ),
    )
    controller.persistence_service.save_character(character)

    controller.move_item(character, "longsword", "backpack", autosave=True)
    controller.equip_item(character, "longsword", EquipmentSlot.MAIN_HAND, autosave=True)
    assert controller.equipment_stats(character)["attack_bonus"] == (0, 0, 0)
    controller.unequip_item(character, EquipmentSlot.MAIN_HAND, autosave=True)
    controller.unequip_item(character, EquipmentSlot.HEAD, autosave=True)

    restored = controller.persistence_service.load_character("fighter")
    sword = next(item for item in restored.inventory if item.item_id == "longsword")
    assert sword.equipped_slot is None
