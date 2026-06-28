import pytest

from dnd_combat_engine.models import InventoryItem, ItemCategory


def test_inventory_item_round_trips_to_plain_data() -> None:
    item = InventoryItem(
        item_id="torch",
        name="Torch",
        quantity=5,
        weight=1.0,
        category=ItemCategory.ADVENTURING_GEAR,
        notes="Burns for 1 hour",
        tags=("light",),
    )

    restored = InventoryItem.from_dict(item.to_dict())

    assert restored == item
    assert restored.total_weight == 5.0


def test_inventory_item_can_change_quantity() -> None:
    item = InventoryItem(item_id="ration", name="Ration", quantity=2)

    assert item.with_quantity(5).quantity == 5
    assert item.quantity == 2


def test_inventory_item_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        InventoryItem(item_id="", name="Torch")
    with pytest.raises(ValueError):
        InventoryItem(item_id="torch", name="")
    with pytest.raises(ValueError):
        InventoryItem(item_id="torch", name="Torch", quantity=0)
    with pytest.raises(ValueError):
        InventoryItem(item_id="torch", name="Torch", weight=-1)

