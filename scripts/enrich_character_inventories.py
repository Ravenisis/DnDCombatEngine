"""Merge repo-local SRD metadata into every saved character inventory stack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHARACTER_ROOTS = (
    ROOT / "data" / "characters",
    ROOT / "src" / "dnd_combat_engine" / "data" / "characters",
)
CATALOG_PATH = ROOT / "data" / "equipment" / "srd_equipment.json"
ALIASES = {
    "arrows": "arrows_20",
    "bullseye_lantern": "lantern_bullseye",
    "healers_kit": "healer_s_kit",
    "masons_tools": "mason_s_tools",
    "plate": "plate_armor",
    "rations_1_day": "rations",
}
FALLBACKS: dict[str, dict[str, Any]] = {
    "clothes_common": {
        "category": "adventuring_gear",
        "subcategory": "clothing",
        "weight": 3.0,
        "purchase_price_cp": 50,
        "notes": "SRD adventuring gear. A practical set of common clothes.",
        "tags": ["adventuring_gear", "clothing"],
    },
    "holy_symbol": {
        "category": "adventuring_gear",
        "subcategory": "spellcasting_focus",
        "weight": 0.0,
        "purchase_price_cp": 500,
        "notes": (
            "SRD holy symbol. An amulet, emblem, or reliquary used as a "
            "spellcasting focus when the character's class permits it."
        ),
        "tags": ["holy symbol", "spellcasting_focus"],
    },
}


def main() -> int:
    """Enrich development characters and write matching packaged copies."""
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    by_id = {str(item["item_id"]): item for item in catalog}
    source_root = CHARACTER_ROOTS[0]
    for source_path in source_root.glob("*.json"):
        character = json.loads(source_path.read_text(encoding="utf-8"))
        character["inventory"] = [
            enrich_stack(stack, by_id) for stack in character.get("inventory", [])
        ]
        rendered = json.dumps(character, indent=2, sort_keys=True) + "\n"
        for root in CHARACTER_ROOTS:
            (root / source_path.name).write_text(rendered, encoding="utf-8")
    return 0


def enrich_stack(
    stack: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Return an inventory stack with richer rules metadata and preserved state."""
    item_id = str(stack.get("item_id", ""))
    canonical_id = ALIASES.get(item_id, item_id)
    metadata = catalog.get(canonical_id) or FALLBACKS.get(item_id)
    if metadata is None:
        return stack
    result = dict(stack)
    result.update(
        {
            key: metadata[key]
            for key in (
                "category",
                "subcategory",
                "weight",
                "purchase_price_cp",
                "notes",
            )
            if key in metadata
        }
    )
    result["tags"] = sorted(
        {str(tag) for tag in (*stack.get("tags", []), *metadata.get("tags", []))}
    )
    result["subcategory"] = result.get("subcategory") or infer_subcategory(result)
    if item_id == "arrows":
        result["weight"] = float(metadata["weight"]) / 20
        result["purchase_price_cp"] = int(metadata["purchase_price_cp"]) // 20
        result["subcategory"] = "arrow"
    return result


def infer_subcategory(item: dict[str, Any]) -> str:
    """Infer a useful subcategory when the broad SRD catalog has none."""
    name = str(item.get("name", "")).casefold()
    tags = {str(tag).casefold() for tag in item.get("tags", [])}
    if "container" in tags or any(word in name for word in ("bag", "backpack", "pouch")):
        return "container"
    if "gaming set" in tags or "card" in name:
        return "gaming_set"
    if "light_source" in tags or "lantern" in name:
        return "light_source"
    if "healer" in name:
        return "healing_kit"
    if "tool" in tags or "tools" in name:
        return "artisan_or_utility_tool"
    if any(word in name for word in ("rope", "piton")):
        return "climbing_gear"
    if "tinderbox" in name:
        return "firemaking_gear"
    if "waterskin" in name:
        return "container"
    return str(item.get("category", "other"))


if __name__ == "__main__":
    raise SystemExit(main())
