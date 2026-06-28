"""Inventory controller workflows."""

from __future__ import annotations

from dataclasses import dataclass

from dnd_combat_engine.models.character import Character
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

