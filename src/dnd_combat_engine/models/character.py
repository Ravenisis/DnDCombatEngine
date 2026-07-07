"""Character model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from dnd_combat_engine.models.abilities import AbilityScores
from dnd_combat_engine.models.conditions import Condition, ConditionName
from dnd_combat_engine.models.currency import CurrencyPurse
from dnd_combat_engine.models.equipment import Armor, Weapon
from dnd_combat_engine.models.hit_points import HitPoints
from dnd_combat_engine.models.inventory import InventoryItem
from dnd_combat_engine.models.resources import ResourcePool
from dnd_combat_engine.models.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_FIELD


@dataclass(slots=True)
class Character:
    """A character data model with no combat workflow logic."""

    character_id: str
    name: str
    hit_points: HitPoints
    abilities: AbilityScores = field(default_factory=AbilityScores)
    level: int = 1
    skills: tuple[str, ...] = field(default_factory=tuple)
    inventory: tuple[InventoryItem, ...] = field(default_factory=tuple)
    weapons: tuple[Weapon, ...] = field(default_factory=tuple)
    armor: Armor | None = None
    features: tuple[str, ...] = field(default_factory=tuple)
    conditions: tuple[Condition, ...] = field(default_factory=tuple)
    resources: dict[str, ResourcePool] = field(default_factory=dict)
    currency: CurrencyPurse = field(default_factory=CurrencyPurse)
    saving_throw_proficiencies: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate character identity and level."""
        if not self.character_id:
            raise ValueError("character_id is required")
        if not self.name:
            raise ValueError("name is required")
        if self.level < 1:
            raise ValueError("level must be at least 1")

    def to_dict(self) -> dict[str, object]:
        """Serialize the character to plain JSON-compatible data."""
        return {
            SCHEMA_VERSION_FIELD: CURRENT_SCHEMA_VERSION,
            "character_id": self.character_id,
            "name": self.name,
            "hit_points": self.hit_points.to_dict(),
            "abilities": self.abilities.to_dict(),
            "level": self.level,
            "skills": list(self.skills),
            "inventory": [item.to_dict() for item in self.inventory],
            "weapons": [weapon.to_dict() for weapon in self.weapons],
            "armor": self.armor.to_dict() if self.armor else None,
            "features": list(self.features),
            "conditions": [condition.to_dict() for condition in self.conditions],
            "resources": {
                name: resource.to_dict() for name, resource in self.resources.items()
            },
            "currency": self.currency.to_dict(),
            "saving_throw_proficiencies": list(self.saving_throw_proficiencies),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a character from JSON-compatible data."""
        armor_data = data.get("armor")
        return cls(
            character_id=str(data["character_id"]),
            name=str(data["name"]),
            hit_points=HitPoints.from_dict(data["hit_points"]),  # type: ignore[arg-type]
            abilities=AbilityScores.from_dict(data["abilities"]),  # type: ignore[arg-type]
            level=int(data.get("level", 1)),
            skills=tuple(str(item) for item in data.get("skills", [])),
            inventory=tuple(_inventory_item_from_data(item) for item in data.get("inventory", [])),
            weapons=tuple(
                Weapon.from_dict(item) for item in data.get("weapons", [])  # type: ignore[arg-type]
            ),
            armor=Armor.from_dict(armor_data) if isinstance(armor_data, dict) else None,
            features=tuple(str(item) for item in data.get("features", [])),
            conditions=tuple(
                _condition_from_data(item) for item in data.get("conditions", [])
            ),
            resources={
                str(key): _resource_from_data(str(key), value)
                for key, value in data.get("resources", {}).items()
            },
            currency=CurrencyPurse.from_dict(data.get("currency", {})),  # type: ignore[arg-type]
            saving_throw_proficiencies=tuple(
                str(item) for item in data.get("saving_throw_proficiencies", [])
            ),
        )


def _condition_from_data(data: object) -> Condition:
    if isinstance(data, dict):
        return Condition.from_dict(data)
    return Condition(ConditionName(str(data)))


def _inventory_item_from_data(data: object) -> InventoryItem:
    if isinstance(data, dict):
        return InventoryItem.from_dict(data)
    name = str(data)
    return InventoryItem(item_id=name, name=name)


def _resource_from_data(name: str, data: object) -> ResourcePool:
    if isinstance(data, dict):
        return ResourcePool.from_dict(data)
    value = int(data)
    return ResourcePool(name=name, current=value, maximum=value)
