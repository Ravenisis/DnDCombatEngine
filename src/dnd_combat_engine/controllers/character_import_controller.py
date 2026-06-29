"""Controller workflows for imported character sheets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dnd_combat_engine.models import Campaign, Character
from dnd_combat_engine.models.imports import CharacterImportDraft
from dnd_combat_engine.services import CampaignService, CharacterImportService, PersistenceService


@dataclass(frozen=True, slots=True)
class CharacterImportResult:
    """Result of importing and linking a character."""

    draft: CharacterImportDraft
    character: Character
    campaign: Campaign


@dataclass(frozen=True, slots=True)
class CharacterImportController:
    """UI-facing imported character workflow coordinator."""

    import_service: CharacterImportService
    campaign_service: CampaignService
    persistence_service: PersistenceService

    def preview_pdf(self, pdf_path: Path | str) -> CharacterImportDraft:
        """Parse a PDF into a reviewable character draft."""
        return self.import_service.import_pdf(pdf_path)

    def import_pdf_to_campaign(
        self,
        pdf_path: Path | str,
        campaign_id: str,
        character_id: str | None = None,
    ) -> CharacterImportResult:
        """Import a PDF sheet, save the character, and link it to a campaign."""
        draft = self.preview_pdf(pdf_path)
        campaign = self.persistence_service.load_campaign(campaign_id)
        resolved_id = character_id or self._next_character_id(draft.name)
        character = draft.to_character(resolved_id)
        self.persistence_service.save_character(character)
        updated_campaign = self.campaign_service.add_character(campaign, character.character_id)
        self.persistence_service.save_campaign(updated_campaign)
        return CharacterImportResult(draft, character, updated_campaign)

    def _next_character_id(self, name: str) -> str:
        base = _slug(name) or "imported_character"
        existing = set(self.persistence_service.list_character_ids())
        if base not in existing:
            return base
        counter = 2
        while f"{base}_{counter}" in existing:
            counter += 1
        return f"{base}_{counter}"


def _slug(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

