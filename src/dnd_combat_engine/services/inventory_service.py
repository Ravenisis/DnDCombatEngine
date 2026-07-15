"""Inventory business operations."""

from __future__ import annotations

import re

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.equipment import EquipmentSlot
from dnd_combat_engine.models.inventory import InventoryItem

EQUIPMENT_STAT_ORDER = (
    "armor_class",
    "attack_bonus",
    "damage_bonus",
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
    "walking_speed",
)


class InventoryService:
    """Manage character inventory without embedding item behavior in Character."""

    def add_item(self, character: Character, item: InventoryItem) -> None:
        """Add an item stack to a character inventory."""
        existing = character.inventory
        updated = []
        merged = False
        for carried in existing:
            if carried.item_id == item.item_id:
                updated.append(carried.with_quantity(carried.quantity + item.quantity))
                merged = True
            else:
                updated.append(carried)
        if not merged:
            updated.append(item)
        character.inventory = tuple(updated)

    def remove_item(self, character: Character, item_id: str, quantity: int = 1) -> bool:
        """Remove a quantity of an item and return whether the full amount was removed."""
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        self._normalize_locations(character)
        updated = []
        removed = False
        for item in character.inventory:
            if item.item_id != item_id:
                updated.append(item)
                continue
            if item.quantity < quantity:
                updated.append(item)
                continue
            removed = True
            remaining = item.quantity - quantity
            if remaining:
                updated.append(item.with_quantity(remaining))
        if removed and not any(item.item_id == item_id for item in updated):
            updated = [
                item.stored_in(None) if item.container_id == item_id else item
                for item in updated
            ]
        character.inventory = tuple(updated)
        return removed

    def quantity(self, character: Character, item_id: str) -> int:
        """Return the quantity carried for an item id."""
        return sum(item.quantity for item in character.inventory if item.item_id == item_id)

    def has_item(self, character: Character, item_id: str, quantity: int = 1) -> bool:
        """Return whether a character carries at least a quantity of an item."""
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        return self.quantity(character, item_id) >= quantity

    def total_weight(self, character: Character) -> float:
        """Return total carried inventory weight."""
        return sum(item.total_weight for item in character.inventory)

    def move_item(
        self,
        character: Character,
        item_id: str,
        container_id: str | None,
    ) -> InventoryItem:
        """Move one item stack into a container or back to carried inventory."""
        self._normalize_locations(character)
        item = self._item(character, item_id)
        if container_id is not None:
            container = self._item(character, container_id)
            if not _is_container(container):
                raise ValueError(f"{container.name} is not a container")
            if item_id == container_id or self._is_descendant(character, container_id, item_id):
                raise ValueError("containers cannot be moved inside themselves")
        moved = item.stored_in(container_id)
        self._replace(character, moved)
        return moved

    def equip_item(
        self,
        character: Character,
        item_id: str,
        slot: EquipmentSlot,
    ) -> InventoryItem:
        """Equip an inventory item in a compatible body slot."""
        self._normalize_locations(character)
        item = self._item(character, item_id)
        if not _supports_slot(item, slot):
            raise ValueError(f"{item.name} cannot be equipped in {slot.value.replace('_', ' ')}")
        updated = [
            carried.equipped_in(None) if carried.equipped_slot is slot else carried
            for carried in character.inventory
        ]
        character.inventory = tuple(updated)
        equipped = item.equipped_in(slot)
        self._replace(character, equipped)
        return equipped

    def compatible_items(
        self,
        character: Character,
        slot: EquipmentSlot,
    ) -> tuple[InventoryItem, ...]:
        """Return unequipped inventory items that can be equipped in a slot."""
        self._normalize_locations(character)
        return tuple(
            sorted(
                (
                    item
                    for item in character.inventory
                    if item.equipped_slot is None and _supports_slot(item, slot)
                ),
                key=lambda item: item.name.casefold(),
            )
        )

    def unequip_item(self, character: Character, slot: EquipmentSlot) -> InventoryItem | None:
        """Return the item in a body slot to carried inventory."""
        item = next((item for item in character.inventory if item.equipped_slot is slot), None)
        if item is None:
            return None
        unequipped = item.equipped_in(None)
        self._replace(character, unequipped)
        return unequipped

    def equipment_stats(self, character: Character) -> dict[str, tuple[int, int, int]]:
        """Return base, gear bonus, and resulting values for equipment statistics."""
        unarmored_ac = 10 + character.abilities.modifier("dexterity")
        base = {
            "armor_class": unarmored_ac,
            "attack_bonus": character.proficiency_bonus or 0,
            "damage_bonus": 0,
            "strength": character.abilities.strength,
            "dexterity": character.abilities.dexterity,
            "constitution": character.abilities.constitution,
            "intelligence": character.abilities.intelligence,
            "wisdom": character.abilities.wisdom,
            "charisma": character.abilities.charisma,
            "walking_speed": character.walking_speed or 30,
        }
        gear = dict.fromkeys(EQUIPMENT_STAT_ORDER, 0)
        for item in character.inventory:
            if item.equipped_slot is None:
                continue
            if item.equipped_slot is EquipmentSlot.CHEST:
                armor_class = _armor_class(item, character.abilities.modifier("dexterity"))
                if armor_class is not None:
                    gear["armor_class"] += armor_class - unarmored_ac
            for name, value in _item_modifiers(item).items():
                if name in gear:
                    gear[name] += value
        return {name: (base[name], gear[name], base[name] + gear[name]) for name in base}

    @staticmethod
    def _item(character: Character, item_id: str) -> InventoryItem:
        item = next((item for item in character.inventory if item.item_id == item_id), None)
        if item is None:
            raise ValueError(f"inventory item not found: {item_id}")
        return item

    @staticmethod
    def _replace(character: Character, replacement: InventoryItem) -> None:
        character.inventory = tuple(
            replacement if item.item_id == replacement.item_id else item
            for item in character.inventory
        )

    @staticmethod
    def _normalize_locations(character: Character) -> None:
        if any(
            item.container_id is not None or item.equipped_slot is not None
            for item in character.inventory
        ):
            return
        current_container: str | None = None
        normalized = []
        for item in character.inventory:
            if _is_container(item):
                current_container = item.item_id
                normalized.append(item)
            else:
                normalized.append(item.stored_in(current_container))
        character.inventory = tuple(normalized)

    @staticmethod
    def _is_descendant(character: Character, item_id: str, possible_ancestor: str) -> bool:
        by_id = {item.item_id: item for item in character.inventory}
        current = by_id.get(item_id)
        visited: set[str] = set()
        while current is not None and current.container_id is not None:
            if current.container_id == possible_ancestor:
                return True
            if current.container_id in visited:
                return True
            visited.add(current.container_id)
            current = by_id.get(current.container_id)
        return False


def _is_container(item: InventoryItem) -> bool:
    normalized = item.name.casefold().replace(" ", "_")
    return "container" in item.tags or any(
        name in normalized for name in ("bag", "backpack", "pouch", "quiver", "chest")
    )


def _supports_slot(item: InventoryItem, slot: EquipmentSlot) -> bool:
    text = " ".join((item.name, item.subcategory, *item.tags)).casefold()
    if slot is EquipmentSlot.CHEST:
        return item.category.value == "armor" and "shield" not in text
    if slot in {EquipmentSlot.MAIN_HAND, EquipmentSlot.OFF_HAND}:
        return item.category.value == "weapon" or "shield" in text or "focus" in text
    keywords = {
        EquipmentSlot.HEAD: ("helm", "helmet", "hat", "circlet", "head"),
        EquipmentSlot.NECK: ("amulet", "necklace", "neck"),
        EquipmentSlot.BACK: ("cloak", "cape", "back"),
        EquipmentSlot.HANDS: ("glove", "gauntlet", "hands"),
        EquipmentSlot.WAIST: ("belt", "waist"),
        EquipmentSlot.LEGS: ("legging", "pants", "legs"),
        EquipmentSlot.FEET: ("boot", "shoe", "slipper", "feet"),
        EquipmentSlot.RING_LEFT: ("ring",),
        EquipmentSlot.RING_RIGHT: ("ring",),
    }
    return any(keyword in text for keyword in keywords.get(slot, ()))


def _item_modifiers(item: InventoryItem) -> dict[str, int]:
    modifiers = dict(item.modifiers)
    for tag in item.tags:
        if tag.startswith("bonus:+") and tag.removeprefix("bonus:+").isdigit():
            bonus = int(tag.removeprefix("bonus:+"))
            if item.category.value == "weapon":
                modifiers["attack_bonus"] = modifiers.get("attack_bonus", 0) + bonus
                modifiers["damage_bonus"] = modifiers.get("damage_bonus", 0) + bonus
            elif item.category.value == "armor":
                modifiers["armor_class"] = modifiers.get("armor_class", 0) + bonus
        if tag.startswith("ac:+") and tag.removeprefix("ac:+").isdigit():
            modifiers["armor_class"] = modifiers.get("armor_class", 0) + int(
                tag.removeprefix("ac:+")
            )
    return modifiers


def _armor_class(item: InventoryItem, dexterity_modifier: int) -> int | None:
    tag = next((tag for tag in item.tags if tag.startswith("ac:") and "+" not in tag), None)
    if tag is None:
        return None
    match = re.match(r"ac:(\d+)", tag)
    if match is None:
        return None
    armor_class = int(match.group(1))
    if "Dex modifier" in tag:
        dexterity = min(dexterity_modifier, 2) if "max 2" in tag else dexterity_modifier
        armor_class += dexterity
    return armor_class
