"""Add stable inventory categories to the repo-local SRD 5.2.1 equipment catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATHS = (
    ROOT / "data" / "equipment" / "srd_equipment.json",
    ROOT / "src" / "dnd_combat_engine" / "data" / "equipment" / "srd_equipment.json",
)

LIGHT_ARMOR = {"padded armor", "leather armor", "studded leather armor"}
MEDIUM_ARMOR = {"hide armor", "chain shirt", "scale mail", "breastplate", "half plate armor"}
HEAVY_ARMOR = {"ring mail", "chain mail", "splint armor", "plate armor"}
RANGED_WEAPONS = {
    "blowgun",
    "hand crossbow",
    "heavy crossbow",
    "light crossbow",
    "longbow",
    "shortbow",
    "sling",
}
SIMPLE_WEAPONS = {
    "club",
    "dagger",
    "greatclub",
    "handaxe",
    "javelin",
    "light hammer",
    "mace",
    "quarterstaff",
    "sickle",
    "spear",
    "dart",
    "light crossbow",
    "shortbow",
    "sling",
}


def main() -> int:
    """Enrich both development and packaged copies of the equipment catalog."""
    source = json.loads(CATALOG_PATHS[0].read_text(encoding="utf-8"))
    items = [enrich_item(item) for item in source]
    rendered = json.dumps(items, indent=2, ensure_ascii=True) + "\n"
    for path in CATALOG_PATHS:
        path.write_text(rendered, encoding="utf-8")
    return 0


def enrich_item(item: dict[str, Any]) -> dict[str, Any]:
    """Return one catalog entry with a detailed category and subcategory."""
    result = dict(item)
    name = str(result.get("name", "")).casefold()
    tags = {str(tag).casefold() for tag in result.get("tags", [])}
    category = str(result.get("category", "other"))
    if "ammunition" in tags or _looks_like_ammunition(name):
        result["category"] = "ammunition"
        result["subcategory"] = _ammunition_subcategory(name)
    elif category == "weapon":
        result["subcategory"] = _weapon_subcategory(name, tags)
    elif category == "armor":
        result["subcategory"] = _armor_subcategory(name, tags)
    elif category == "consumable":
        result["subcategory"] = _consumable_subcategory(name, tags)
    return result


def _looks_like_ammunition(name: str) -> bool:
    return any(word in name for word in ("arrow", "bolt", "bullet", "ammunition", "needle"))


def _ammunition_subcategory(name: str) -> str:
    if "arrow" in name:
        return "arrow"
    if "bolt" in name:
        return "crossbow_bolt"
    if "bullet" in name:
        return "bullet"
    if "needle" in name:
        return "needle"
    return "special_ammunition"


def _weapon_subcategory(name: str, tags: set[str]) -> str:
    if "magic item" in tags and name not in SIMPLE_WEAPONS | RANGED_WEAPONS:
        return "magic_weapon"
    training = "simple" if name in SIMPLE_WEAPONS else "martial"
    reach = "ranged" if name in RANGED_WEAPONS or "range" in " ".join(tags) else "melee"
    return f"{training}_{reach}_weapon"


def _armor_subcategory(name: str, tags: set[str]) -> str:
    if "shield" in name or "shield" in tags:
        return "shield"
    if name in LIGHT_ARMOR:
        return "light_armor"
    if name in MEDIUM_ARMOR:
        return "medium_armor"
    if name in HEAVY_ARMOR:
        return "heavy_armor"
    return "magic_armor" if "magic item" in tags else "armor"


def _consumable_subcategory(name: str, tags: set[str]) -> str:
    if "potion" in name or "potion" in tags:
        return "potion"
    if "scroll" in name or "scroll" in tags:
        return "spell_scroll"
    if "poison" in name or "poison" in tags or "antitoxin" in name:
        return "poison_and_antitoxin"
    if "healing" in tags:
        return "healing_consumable"
    if any(word in name for word in ("ration", "food", "bead of nourishment")):
        return "food"
    if any(word in name for word in ("candle", "torch", "oil")):
        return "light_source"
    return "magic_consumable" if "magic item" in tags else "adventuring_consumable"


if __name__ == "__main__":
    raise SystemExit(main())
