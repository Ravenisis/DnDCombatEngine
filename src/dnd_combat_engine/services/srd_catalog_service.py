"""SRD catalog loading helpers."""

from __future__ import annotations

from dnd_combat_engine.models.srd_catalog import SrdCatalog, SrdCatalogEntry
from dnd_combat_engine.services.persistence_service import PersistenceService


class SrdCatalogService:
    """Load compact SRD support catalogs from persistence."""

    def __init__(self, persistence_service: PersistenceService) -> None:
        """Create the catalog service."""
        self.persistence_service = persistence_service

    def load(self, catalog_id: str) -> SrdCatalog:
        """Load an SRD catalog by id."""
        return self.persistence_service.load_srd_catalog(catalog_id)

    def entries(self, catalog_id: str) -> tuple[SrdCatalogEntry, ...]:
        """Return all entries for an SRD catalog."""
        return self.load(catalog_id).entries

    def entries_for_owner(self, catalog_id: str, owner: str) -> tuple[SrdCatalogEntry, ...]:
        """Return catalog entries for a class, subclass, or species owner."""
        owner_key = owner.casefold()
        return tuple(
            entry for entry in self.entries(catalog_id) if entry.owner.casefold() == owner_key
        )

    def entries_up_to_level(self, catalog_id: str, level: int) -> tuple[SrdCatalogEntry, ...]:
        """Return entries whose character-level prerequisite is within the requested level."""
        return tuple(
            entry
            for entry in self.entries(catalog_id)
            if entry.level is None or entry.level <= level
        )
