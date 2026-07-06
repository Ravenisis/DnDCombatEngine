"""Inventory models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self


class ItemCategory(StrEnum):
    """Broad item categories for inventory organization."""

    ADVENTURING_GEAR = "adventuring_gear"
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
        )
