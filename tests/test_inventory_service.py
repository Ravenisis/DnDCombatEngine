import pytest

from dnd_combat_engine.models import Character, HitPoints, InventoryItem, ItemCategory
from dnd_combat_engine.services import InventoryService


def make_character() -> Character:
    return Character(
        character_id="rogue-1",
        name="Vale",
        hit_points=HitPoints(current=9, maximum=9),
    )


def test_inventory_service_adds_and_merges_item_stacks() -> None:
    character = make_character()
    service = InventoryService()

    service.add_item(
        character,
        InventoryItem(
            item_id="dagger",
            name="Dagger",
            quantity=1,
            weight=1.0,
            category=ItemCategory.WEAPON,
        ),
    )
    service.add_item(
        character,
        InventoryItem(
            item_id="dagger",
            name="Dagger",
            quantity=2,
            weight=1.0,
            category=ItemCategory.WEAPON,
        ),
    )

    assert service.quantity(character, "dagger") == 3
    assert service.has_item(character, "dagger", quantity=3) is True
    assert service.total_weight(character) == 3.0


def test_inventory_service_removes_partial_and_full_stacks() -> None:
    character = make_character()
    service = InventoryService()
    service.add_item(character, InventoryItem(item_id="ration", name="Ration", quantity=3))

    assert service.remove_item(character, "ration", quantity=2) is True
    assert service.quantity(character, "ration") == 1
    assert service.remove_item(character, "ration", quantity=1) is True
    assert service.has_item(character, "ration") is False


def test_inventory_service_refuses_missing_or_excessive_removal() -> None:
    character = make_character()
    service = InventoryService()
    service.add_item(character, InventoryItem(item_id="potion", name="Potion", quantity=1))

    assert service.remove_item(character, "missing") is False
    assert service.remove_item(character, "potion", quantity=2) is False
    assert service.quantity(character, "potion") == 1


def test_inventory_service_rejects_invalid_quantities() -> None:
    character = make_character()
    service = InventoryService()

    with pytest.raises(ValueError):
        service.remove_item(character, "potion", quantity=0)
    with pytest.raises(ValueError):
        service.has_item(character, "potion", quantity=0)

