from types import SimpleNamespace

import pytest

from dnd_combat_engine.gui.drag_drop import ITEM_MIME_TYPE, item_id_from_mime, set_item_mime_data
from dnd_combat_engine.models import (
    AbilityScores,
    Character,
    EquipmentSlot,
    HitPoints,
    InventoryItem,
    ItemCategory,
)
from dnd_combat_engine.services import InventoryService


def _equipped_character() -> Character:
    return Character(
        "hero",
        "Hero",
        HitPoints(20, 20),
        abilities=AbilityScores(dexterity=14),
        proficiency_bonus=3,
        inventory=(
            InventoryItem("backpack", "Backpack", tags=("container",)),
            InventoryItem("rope", "Rope"),
            InventoryItem("pouch", "Pouch", tags=("container",)),
            InventoryItem("longsword", "Longsword", category=ItemCategory.WEAPON),
            InventoryItem(
                "chain_mail",
                "Chain Mail",
                category=ItemCategory.ARMOR,
                tags=("armor", "ac:16"),
                subcategory="heavy_armor",
            ),
            InventoryItem(
                "shield_plus_one",
                "Shield +1",
                category=ItemCategory.ARMOR,
                tags=("armor", "shield", "ac:+2", "bonus:+1"),
                subcategory="shield",
            ),
        ),
    )


def test_inventory_locations_and_modifiers_round_trip() -> None:
    item = InventoryItem(
        "defender",
        "Defender",
        category=ItemCategory.WEAPON,
        subcategory="magic_weapon",
        container_id="bag",
        modifiers=(("attack_bonus", 2), ("damage_bonus", 2)),
    )

    restored = InventoryItem.from_dict(item.to_dict())

    assert restored == item
    assert restored.stored_in(None).container_id is None
    assert restored.equipped_in(EquipmentSlot.MAIN_HAND).equipped_slot is EquipmentSlot.MAIN_HAND


def test_inventory_service_moves_equips_and_summarizes_gear() -> None:
    character = _equipped_character()
    service = InventoryService()

    moved = service.move_item(character, "longsword", "backpack")
    weapon = service.equip_item(character, moved.item_id, EquipmentSlot.MAIN_HAND)
    service.equip_item(character, "chain_mail", EquipmentSlot.CHEST)
    service.equip_item(character, "shield_plus_one", EquipmentSlot.OFF_HAND)
    stats = service.equipment_stats(character)

    assert moved.container_id == "backpack"
    assert weapon.container_id is None
    assert weapon.equipped_slot is EquipmentSlot.MAIN_HAND
    assert stats["armor_class"] == (12, 7, 19)
    assert stats["attack_bonus"] == (3, 0, 3)
    assert service.unequip_item(character, EquipmentSlot.MAIN_HAND) is not None
    assert service.unequip_item(character, EquipmentSlot.HEAD) is None


def test_inventory_service_rejects_bad_storage_and_equipment() -> None:
    character = _equipped_character()
    service = InventoryService()

    with pytest.raises(ValueError, match="not a container"):
        service.move_item(character, "longsword", "rope")
    with pytest.raises(ValueError, match="cannot be equipped"):
        service.equip_item(character, "rope", EquipmentSlot.HEAD)
    with pytest.raises(ValueError, match="not found"):
        service.move_item(character, "missing", None)
    with pytest.raises(ValueError, match="inside themselves"):
        service.move_item(character, "backpack", "backpack")


def test_removing_a_container_returns_its_contents_to_carried_inventory() -> None:
    character = _equipped_character()
    service = InventoryService()
    service.move_item(character, "rope", "pouch")

    assert service.remove_item(character, "pouch") is True

    rope = next(item for item in character.inventory if item.item_id == "rope")
    assert rope.container_id is None


def test_drag_drop_payload_round_trips_and_rejects_other_mime_types() -> None:
    class ByteArray(bytes):
        pass

    class MimeData:
        def __init__(self) -> None:
            self.values = {}

        def setData(self, name, value) -> None:
            self.values[name] = value

        def hasFormat(self, name) -> bool:
            return name in self.values

        def data(self, name):
            return self.values[name]

    qt = SimpleNamespace(QtCore=SimpleNamespace(QByteArray=ByteArray))
    mime = MimeData()

    assert item_id_from_mime(mime) is None
    set_item_mime_data(qt, mime, "longsword")
    assert mime.hasFormat(ITEM_MIME_TYPE)
    assert item_id_from_mime(mime) == "longsword"
    assert item_id_from_mime(None) is None
