"""SRD catalog models for rules support coverage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from dnd_combat_engine.models.rules import RuleSource
from dnd_combat_engine.models.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_FIELD


@dataclass(frozen=True, slots=True)
class SrdCatalogEntry:
    """A compact SRD feature, trait, option, or spell catalog entry."""

    entry_id: str
    name: str
    entry_type: str
    owner: str = ""
    level: int | None = None
    spell_level: int | None = None
    school: str = ""
    classes: tuple[str, ...] = field(default_factory=tuple)
    source_reference: str = ""
    automation_status: str = "cataloged"

    def __post_init__(self) -> None:
        """Validate required catalog fields."""
        if not self.entry_id:
            raise ValueError("entry_id is required")
        if not self.name:
            raise ValueError("name is required")
        if not self.entry_type:
            raise ValueError("entry_type is required")
        if self.level is not None and self.level < 1:
            raise ValueError("level must be at least 1")
        if self.spell_level is not None and not 0 <= self.spell_level <= 9:
            raise ValueError("spell level must be between 0 and 9")

    def to_dict(self) -> dict[str, object]:
        """Serialize the catalog entry."""
        return {
            "entry_id": self.entry_id,
            "name": self.name,
            "entry_type": self.entry_type,
            "owner": self.owner,
            "level": self.level,
            "spell_level": self.spell_level,
            "school": self.school,
            "classes": list(self.classes),
            "source_reference": self.source_reference,
            "automation_status": self.automation_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a catalog entry from JSON data."""
        level = data.get("level")
        spell_level = data.get("spell_level")
        return cls(
            entry_id=str(data["entry_id"]),
            name=str(data["name"]),
            entry_type=str(data["entry_type"]),
            owner=str(data.get("owner", "")),
            level=int(level) if level is not None else None,
            spell_level=int(spell_level) if spell_level is not None else None,
            school=str(data.get("school", "")),
            classes=tuple(str(item) for item in data.get("classes", [])),
            source_reference=str(data.get("source_reference", "")),
            automation_status=str(data.get("automation_status", "cataloged")),
        )


@dataclass(frozen=True, slots=True)
class SrdCatalog:
    """A compact SRD catalog generated from source markdown."""

    catalog_id: str
    title: str
    entries: tuple[SrdCatalogEntry, ...]
    source: RuleSource
    max_character_level: int = 10
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate catalog identity and coverage."""
        if not self.catalog_id:
            raise ValueError("catalog_id is required")
        if not self.title:
            raise ValueError("title is required")
        if self.max_character_level < 1:
            raise ValueError("max character level must be at least 1")

    def to_dict(self) -> dict[str, object]:
        """Serialize the SRD catalog."""
        return {
            SCHEMA_VERSION_FIELD: CURRENT_SCHEMA_VERSION,
            "catalog_id": self.catalog_id,
            "title": self.title,
            "max_character_level": self.max_character_level,
            "notes": self.notes,
            "source": self.source.to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build an SRD catalog from JSON data."""
        return cls(
            catalog_id=str(data["catalog_id"]),
            title=str(data["title"]),
            max_character_level=int(data.get("max_character_level", 10)),
            notes=str(data.get("notes", "")),
            source=RuleSource.from_dict(data["source"]),
            entries=tuple(
                SrdCatalogEntry.from_dict(entry)
                for entry in data.get("entries", [])
                if isinstance(entry, dict)
            ),
        )
