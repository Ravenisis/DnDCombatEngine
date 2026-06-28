"""Inventory business operations."""

from __future__ import annotations

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.inventory import InventoryItem


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

