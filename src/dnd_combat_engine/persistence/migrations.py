"""Schema migrations for persisted JSON documents."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from dnd_combat_engine.models.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_FIELD

JsonPayload = dict[str, Any]
Migration = Callable[[JsonPayload], JsonPayload]


def migrate_character(data: JsonPayload) -> JsonPayload:
    """Migrate a character document to the current schema version."""
    return _migrate_document(data, "character", ())


def migrate_campaign(data: JsonPayload) -> JsonPayload:
    """Migrate a campaign document to the current schema version."""
    return _migrate_document(data, "campaign", ())


def migrate_encounter(data: JsonPayload) -> JsonPayload:
    """Migrate an encounter document to the current schema version."""
    return _migrate_document(data, "encounter", ())


def migrate_monster(data: JsonPayload) -> JsonPayload:
    """Migrate a monster document to the current schema version."""
    return _migrate_document(data, "monster", ())


def migrate_spell(data: JsonPayload) -> JsonPayload:
    """Migrate a spell document to the current schema version."""
    return _migrate_document(data, "spell", ())


def _migrate_document(
    data: JsonPayload,
    document_name: str,
    migrations: tuple[Migration, ...],
) -> JsonPayload:
    migrated = dict(data)
    version = _schema_version(migrated, document_name)
    for target_version, migration in enumerate(migrations, start=1):
        if version < target_version:
            migrated = migration(migrated)
            version = target_version
    migrated[SCHEMA_VERSION_FIELD] = CURRENT_SCHEMA_VERSION
    return migrated


def _schema_version(data: JsonPayload, document_name: str) -> int:
    raw_version = data.get(SCHEMA_VERSION_FIELD, 0)
    try:
        version = int(raw_version)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{document_name} schema_version must be an integer") from exc
    if version < 0:
        raise ValueError(f"{document_name} schema_version cannot be negative")
    if version > CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"{document_name} schema_version {version} is newer than supported "
            f"version {CURRENT_SCHEMA_VERSION}"
        )
    return version
