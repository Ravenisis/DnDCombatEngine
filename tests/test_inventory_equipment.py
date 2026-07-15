from types import SimpleNamespace

import pytest

from dnd_combat_engine.gui import equipment
from dnd_combat_engine.gui.drag_drop import ITEM_MIME_TYPE, item_id_from_mime, set_item_mime_data
from dnd_combat_engine.models import (
    AbilityScores,
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    EquipmentSlot,
    HitPoints,
    InventoryItem,
    ItemCategory,
    Weapon,
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


def test_inventory_service_lists_slot_compatible_unequipped_items() -> None:
    character = _equipped_character()
    service = InventoryService()

    assert [item.name for item in service.compatible_items(character, EquipmentSlot.CHEST)] == [
        "Chain Mail"
    ]
    assert [
        item.name for item in service.compatible_items(character, EquipmentSlot.MAIN_HAND)
    ] == ["Longsword", "Shield +1"]

    service.equip_item(character, "longsword", EquipmentSlot.MAIN_HAND)

    assert [
        item.name for item in service.compatible_items(character, EquipmentSlot.MAIN_HAND)
    ] == ["Shield +1"]


def test_ring_slots_accept_rings_without_substring_false_positives() -> None:
    character = Character(
        "hero",
        "Hero",
        HitPoints(20, 20),
        inventory=(
            InventoryItem("protection", "Ring of Protection", tags=("ring",)),
            InventoryItem("signet", "Signet Ring"),
            InventoryItem("string", "String"),
            InventoryItem("springing", "Boots of Striding and Springing"),
            InventoryItem("ball_bearings", "Ball Bearings"),
            InventoryItem(
                "ring_mail",
                "Ring Mail",
                category=ItemCategory.ARMOR,
                subcategory="heavy_armor",
            ),
        ),
    )
    service = InventoryService()

    compatible = service.compatible_items(character, EquipmentSlot.RING_LEFT)

    assert [item.name for item in compatible] == ["Ring of Protection", "Signet Ring"]
    service.equip_item(character, "protection", EquipmentSlot.RING_LEFT)
    assert service.compatible_items(character, EquipmentSlot.RING_RIGHT) == (
        next(item for item in character.inventory if item.item_id == "signet"),
    )


def test_inventory_service_enriches_legacy_items_and_recovers_owned_weapon() -> None:
    character = Character(
        "hero",
        "Hero",
        HitPoints(20, 20),
        inventory=(
            InventoryItem("plate", "Plate", category=ItemCategory.OTHER),
            InventoryItem("rope", "Rope", container_id="backpack"),
            InventoryItem("rope", "Rope", quantity=2, container_id="backpack"),
            InventoryItem("clothes", "Clothes"),
            InventoryItem("common", "Common"),
        ),
        weapons=(
            Weapon(
                "Warhammer",
                DamageProfile((DamageComponent("1d8", DamageType.BLUDGEONING),)),
            ),
        ),
    )
    references = (
        InventoryItem(
            "plate_armor",
            "Plate Armor",
            weight=65,
            category=ItemCategory.ARMOR,
            notes="Armor Class 18; Strength 15; stealth disadvantage.",
            tags=("armor", "ac:18"),
            purchase_price_cp=150_000,
            subcategory="heavy_armor",
        ),
        InventoryItem(
            "warhammer",
            "Warhammer",
            weight=5,
            category=ItemCategory.WEAPON,
            notes="1d8 bludgeoning; versatile (1d10).",
            tags=("weapon", "damage:1d8 Bludgeoning"),
            purchase_price_cp=1_500,
            subcategory="martial_melee_weapon",
        ),
        InventoryItem(
            "rope",
            "Rope",
            weight=10,
            category=ItemCategory.ADVENTURING_GEAR,
            notes="Fifty feet of hempen rope.",
        ),
        InventoryItem(
            "clothes_common",
            "Clothes, Common",
            weight=3,
            category=ItemCategory.ADVENTURING_GEAR,
            notes="A common travel outfit.",
        ),
    )
    service = InventoryService()

    assert service.enrich_inventory_metadata(character, references) is True
    assert service.enrich_inventory_metadata(character, references) is False

    by_id = {item.item_id: item for item in character.inventory}
    assert by_id["plate"].category is ItemCategory.ARMOR
    assert by_id["plate"].subcategory == "heavy_armor"
    assert by_id["plate"].weight == 65
    assert by_id["rope"].quantity == 3
    assert by_id["rope"].container_id == "backpack"
    assert "common" not in by_id
    assert by_id["clothes_common"].name == "Clothes, Common"
    assert by_id["warhammer"].category is ItemCategory.WEAPON
    assert service.compatible_items(character, EquipmentSlot.CHEST) == (by_id["plate"],)
    assert by_id["warhammer"] in service.compatible_items(
        character, EquipmentSlot.MAIN_HAND
    )


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


def test_equipment_slot_menu_lists_compatible_items_and_unequip() -> None:
    class Signal:
        def connect(self, callback) -> None:
            self.callback = callback

    class Action:
        def __init__(self, text: str) -> None:
            self.text = text
            self.triggered = Signal()

        def setToolTip(self, value: str) -> None:  # noqa: N802
            self.tooltip = value

        def setEnabled(self, value: bool) -> None:  # noqa: N802
            self.enabled = value

    class Menu:
        last = None

        def __init__(self, parent) -> None:
            self.parent = parent
            self.actions = []
            Menu.last = self

        def addAction(self, text: str):  # noqa: N802
            action = Action(text)
            self.actions.append(action)
            return action

        def addSeparator(self) -> None:  # noqa: N802
            self.separated = True

        def exec(self, position) -> None:
            self.position = position

    qt = SimpleNamespace(QtWidgets=SimpleNamespace(QMenu=Menu))
    sword = InventoryItem("longsword", "Longsword", category=ItemCategory.WEAPON)
    shield = InventoryItem("shield", "Shield", category=ItemCategory.ARMOR)
    calls = []
    event = SimpleNamespace(globalPosition=lambda: SimpleNamespace(toPoint=lambda: (5, 6)))

    equipment._show_slot_menu(  # noqa: SLF001
        qt,
        object(),
        event,
        EquipmentSlot.MAIN_HAND,
        shield,
        (sword,),
        lambda item_id, slot: calls.append((item_id, slot)),
        lambda slot: calls.append(("unequip", slot)),
    )

    assert [action.text for action in Menu.last.actions] == [
        "Equip Longsword",
        "Unequip Shield",
    ]
    Menu.last.actions[0].triggered.callback()
    Menu.last.actions[1].triggered.callback()
    assert calls == [
        ("longsword", EquipmentSlot.MAIN_HAND),
        ("unequip", EquipmentSlot.MAIN_HAND),
    ]

    equipment._show_slot_menu(  # noqa: SLF001
        qt,
        object(),
        SimpleNamespace(globalPos=lambda: (8, 9)),
        EquipmentSlot.HEAD,
        None,
        (),
        None,
        None,
    )

    assert Menu.last.actions[0].text == "No compatible inventory items"
    assert Menu.last.actions[0].enabled is False
    assert Menu.last.position == (8, 9)


def test_equipment_mouse_helpers_support_qt_position_variants() -> None:
    position = SimpleNamespace(toPoint=lambda: (3, 4))

    assert equipment._event_global_position(  # noqa: SLF001
        SimpleNamespace(position=lambda: position)
    ) == (3, 4)
    assert equipment._event_global_position(object()) is None  # noqa: SLF001

    qt = SimpleNamespace(
        QtCore=SimpleNamespace(
            Qt=SimpleNamespace(MouseButton=SimpleNamespace(RightButton=2))
        )
    )
    assert equipment._is_right_click(qt, SimpleNamespace(button=lambda: 2))  # noqa: SLF001
    assert not equipment._is_right_click(qt, SimpleNamespace(button=lambda: 1))  # noqa: SLF001
