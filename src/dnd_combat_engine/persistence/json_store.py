"""JSON file persistence primitives."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonFileStore:
    """Small JSON document store organized by collection folders."""

    def __init__(self, root: Path | str) -> None:
        """Create a store rooted at a data directory."""
        self.root = Path(root)

    def save(self, collection: str, entity_id: str, payload: dict[str, Any]) -> Path:
        """Save a JSON payload and return the file path."""
        if not collection:
            raise ValueError("collection is required")
        if not entity_id:
            raise ValueError("entity_id is required")
        directory = self.root / collection
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{entity_id}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def load(self, collection: str, entity_id: str) -> dict[str, Any]:
        """Load a JSON payload by collection and id."""
        path = self.root / collection / f"{entity_id}.json"
        with path.open(encoding="utf-8-sig") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return data

    def list_ids(self, collection: str) -> list[str]:
        """List document ids for a collection."""
        directory = self.root / collection
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob("*.json"))
