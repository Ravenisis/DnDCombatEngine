"""Inventory models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from dnd_combat_engine.models.equipment import EquipmentSlot


class ItemCategory(StrEnum):
    """Broad item categories for inventory organization."""

    ADVENTURING_GEAR = "adventuring_gear"
    AMMUNITION = "ammunition"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    TOOL = "tool"
    TREASURE = "treasure"
    WEAPON = "weapon"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class InventoryItem:
    """A stackable item carried by a character."""

    item_id: str
    name: str
    quantity: int = 1
    weight: float = 0.0
    category: ItemCategory = ItemCategory.OTHER
    notes: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    purchase_price_cp: int = 0
    subcategory: str = ""
    container_id: str | None = None
    equipped_slot: EquipmentSlot | None = None
    modifiers: tuple[tuple[str, int], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate item identity and quantities."""
        if not self.item_id:
            raise ValueError("item_id is required")
        if not self.name:
            raise ValueError("name is required")
        if self.quantity < 1:
            raise ValueError("quantity must be at least 1")
        if self.weight < 0:
            raise ValueError("weight cannot be negative")
        if self.purchase_price_cp < 0:
            raise ValueError("purchase_price_cp cannot be negative")
        if self.container_id == self.item_id:
            raise ValueError("an item cannot contain itself")
        if not all(name and isinstance(value, int) for name, value in self.modifiers):
            raise ValueError("modifiers must contain named integer values")

    @property
    def total_weight(self) -> float:
        """Return total weight for this item stack."""
        return self.quantity * self.weight

    def with_quantity(self, quantity: int) -> Self:
        """Return a copy of this item with a new quantity."""
        return type(self)(
            item_id=self.item_id,
            name=self.name,
            quantity=quantity,
            weight=self.weight,
            category=self.category,
            notes=self.notes,
            tags=self.tags,
            purchase_price_cp=self.purchase_price_cp,
            subcategory=self.subcategory,
            container_id=self.container_id,
            equipped_slot=self.equipped_slot,
            modifiers=self.modifiers,
        )

    def stored_in(self, container_id: str | None) -> Self:
        """Return this stack stored in a container or in carried inventory."""
        return type(self)(
            item_id=self.item_id,
            name=self.name,
            quantity=self.quantity,
            weight=self.weight,
            category=self.category,
            notes=self.notes,
            tags=self.tags,
            purchase_price_cp=self.purchase_price_cp,
            subcategory=self.subcategory,
            container_id=container_id,
            equipped_slot=None,
            modifiers=self.modifiers,
        )

    def equipped_in(self, slot: EquipmentSlot | None) -> Self:
        """Return this stack equipped in a slot or returned to carried inventory."""
        return type(self)(
            item_id=self.item_id,
            name=self.name,
            quantity=self.quantity,
            weight=self.weight,
            category=self.category,
            notes=self.notes,
            tags=self.tags,
            purchase_price_cp=self.purchase_price_cp,
            subcategory=self.subcategory,
            container_id=None,
            equipped_slot=slot,
            modifiers=self.modifiers,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the inventory item to plain JSON-compatible data."""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "quantity": self.quantity,
            "weight": self.weight,
            "category": self.category.value,
            "notes": self.notes,
            "tags": list(self.tags),
            "purchase_price_cp": self.purchase_price_cp,
            "subcategory": self.subcategory,
            "container_id": self.container_id,
            "equipped_slot": self.equipped_slot.value if self.equipped_slot else None,
            "modifiers": dict(self.modifiers),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build an inventory item from JSON-compatible data."""
        return cls(
            item_id=str(data["item_id"]),
            name=str(data["name"]),
            quantity=int(data.get("quantity", 1)),
            weight=float(data.get("weight", 0.0)),
            category=ItemCategory(str(data.get("category", ItemCategory.OTHER.value))),
            notes=str(data["notes"]) if data.get("notes") is not None else None,
            tags=tuple(str(tag) for tag in data.get("tags", [])),
            purchase_price_cp=int(data.get("purchase_price_cp", 0)),
            subcategory=str(data.get("subcategory", "")),
            container_id=(
                str(data["container_id"]) if data.get("container_id") is not None else None
            ),
            equipped_slot=(
                EquipmentSlot(str(data["equipped_slot"]))
                if data.get("equipped_slot") is not None
                else None
            ),
            modifiers=tuple(
                (str(name), int(value))
                for name, value in _modifier_items(data.get("modifiers", {}))
            ),
        )


def _modifier_items(value: object) -> tuple[tuple[object, object], ...]:
    if isinstance(value, dict):
        return tuple(value.items())
    if isinstance(value, list):
        return tuple(tuple(item) for item in value if isinstance(item, list) and len(item) == 2)
    return ()
