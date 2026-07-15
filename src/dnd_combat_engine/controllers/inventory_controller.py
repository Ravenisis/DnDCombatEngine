"""Inventory controller workflows."""

from __future__ import annotations

from dataclasses import dataclass

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.equipment import EquipmentSlot
from dnd_combat_engine.models.inventory import InventoryItem
from dnd_combat_engine.services.inventory_service import InventoryService
from dnd_combat_engine.services.persistence_service import PersistenceService


@dataclass(frozen=True, slots=True)
class InventoryController:
    """UI-facing inventory workflow coordinator."""

    inventory_service: InventoryService
    persistence_service: PersistenceService

    def add_item(
        self,
        character: Character,
        item: InventoryItem,
        autosave: bool = False,
    ) -> None:
        """Add an item to a character and optionally save it."""
        self.inventory_service.add_item(character, item)
        if autosave:
            self.persistence_service.save_character(character)

    def remove_item(
        self,
        character: Character,
        item_id: str,
        quantity: int = 1,
        autosave: bool = False,
    ) -> bool:
        """Remove an item quantity from a character and optionally save it."""
        removed = self.inventory_service.remove_item(character, item_id, quantity)
        if autosave:
            self.persistence_service.save_character(character)
        return removed

    def carried_weight(self, character: Character) -> float:
        """Return total carried inventory weight."""
        return self.inventory_service.total_weight(character)

    def move_item(
        self,
        character: Character,
        item_id: str,
        container_id: str | None,
        autosave: bool = False,
    ) -> InventoryItem:
        """Move an item stack between carried storage locations."""
        item = self.inventory_service.move_item(character, item_id, container_id)
        if autosave:
            self.persistence_service.save_character(character)
        return item

    def equip_item(
        self,
        character: Character,
        item_id: str,
        slot: EquipmentSlot,
        autosave: bool = False,
    ) -> InventoryItem:
        """Equip an item in a body slot."""
        item = self.inventory_service.equip_item(character, item_id, slot)
        if autosave:
            self.persistence_service.save_character(character)
        return item

    def unequip_item(
        self,
        character: Character,
        slot: EquipmentSlot,
        autosave: bool = False,
    ) -> InventoryItem | None:
        """Move equipped gear back to carried inventory."""
        item = self.inventory_service.unequip_item(character, slot)
        if autosave and item is not None:
            self.persistence_service.save_character(character)
        return item

    def equipment_stats(self, character: Character) -> dict[str, tuple[int, int, int]]:
        """Return base and equipment-adjusted character statistics."""
        return self.inventory_service.equipment_stats(character)
