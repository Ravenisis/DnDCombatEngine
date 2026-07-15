"""Application wiring helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from dnd_combat_engine.controllers import (
    BetaReportController,
    CampaignController,
    CharacterController,
    CharacterImportController,
    CombatController,
    CombatLogController,
    CompendiumController,
    DiceController,
    EncounterController,
    InventoryController,
)
from dnd_combat_engine.models.inventory import InventoryItem
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.rules import (
    BlessFeature,
    DivineSmiteFeature,
    FeatureEngine,
    GreatWeaponMasterFeature,
    HexFeature,
    HuntersMarkFeature,
    RageFeature,
    SharpshooterFeature,
    SneakAttackFeature,
)
from dnd_combat_engine.services import (
    BetaReportService,
    CampaignService,
    CharacterImportService,
    CharacterService,
    CombatLogService,
    CombatService,
    DiceService,
    EncounterService,
    HostedCampaignBackend,
    InitiativeService,
    InventoryService,
    LocalHostedCampaignBackend,
    MonsterService,
    PersistenceService,
    SpellService,
    UserTokenStore,
)
from dnd_combat_engine.utils.paths import bundled_data_root, default_data_root, user_data_root


@dataclass(frozen=True, slots=True)
class DnDCombatEngineApp:
    """Container for UI-facing controllers."""

    campaigns: CampaignController
    characters: CharacterController
    character_imports: CharacterImportController
    combat: CombatController
    combat_log: CombatLogController
    compendium: CompendiumController
    dice: DiceController
    encounters: EncounterController
    inventory: InventoryController
    beta_reports: BetaReportController
    hosted_campaigns: HostedCampaignBackend


def create_app(data_root: Path | str | None = None) -> DnDCombatEngineApp:
    """Create a fully wired application controller container."""
    resolved_data_root = Path(data_root) if data_root is not None else default_data_root()
    dice_service = DiceService()
    persistence_service = PersistenceService(JsonFileStore(resolved_data_root))
    inventory_service = InventoryService()
    _upgrade_saved_inventory_metadata(persistence_service, inventory_service)
    feature_engine = FeatureEngine(
        [
            BlessFeature(),
            DivineSmiteFeature(),
            GreatWeaponMasterFeature(),
            HexFeature(),
            HuntersMarkFeature(),
            RageFeature(),
            SharpshooterFeature(),
            SneakAttackFeature(),
        ]
    )
    return DnDCombatEngineApp(
        campaigns=CampaignController(CampaignService(), persistence_service),
        characters=CharacterController(CharacterService(), persistence_service),
        character_imports=CharacterImportController(
            CharacterImportService(),
            CampaignService(),
            persistence_service,
        ),
        combat=CombatController(CombatService(dice_service, feature_engine)),
        combat_log=CombatLogController(CombatLogService()),
        compendium=CompendiumController(MonsterService(), SpellService(), persistence_service),
        dice=DiceController(dice_service),
        encounters=EncounterController(
            EncounterService(),
            InitiativeService(dice_service),
            persistence_service,
        ),
        inventory=InventoryController(inventory_service, persistence_service),
        beta_reports=BetaReportController(
            BetaReportService(UserTokenStore(_github_token_path())),
            _default_beta_report_path(resolved_data_root),
        ),
        hosted_campaigns=LocalHostedCampaignBackend(persistence_service),
    )


def _default_beta_report_path(data_root: Path) -> Path:
    """Return the best local beta report target for the current runtime."""
    project_root = data_root.parent if data_root.name == "data" else data_root
    if (project_root / "pyproject.toml").exists():
        return project_root / "BETA_TESTER_REPORTS.md"
    return data_root / "BETA_TESTER_REPORTS.md"


def _github_token_path() -> Path:
    """Return a per-user path outside the repository for encrypted credentials."""
    return user_data_root().parent / "settings" / "github_bug_report_token.bin"


def _upgrade_saved_inventory_metadata(
    persistence: PersistenceService,
    inventory: InventoryService,
) -> None:
    """Enrich legacy saved inventory from the current bundled item references."""
    references = _bundled_inventory_references()
    if not references:
        return
    for character_id in persistence.list_character_ids():
        try:
            character = persistence.load_character(character_id)
            if inventory.enrich_inventory_metadata(character, references):
                persistence.save_character(character)
        except (KeyError, OSError, TypeError, ValueError):
            # A damaged save must not prevent the rest of the application from opening.
            continue


def _bundled_inventory_references() -> tuple[InventoryItem, ...]:
    """Load canonical SRD and bundled-character inventory metadata."""
    root = bundled_data_root()
    references: list[InventoryItem] = []
    catalog = root / "equipment" / "srd_equipment.json"
    try:
        raw_catalog = json.loads(catalog.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw_catalog = []
    if isinstance(raw_catalog, list):
        for raw_item in raw_catalog:
            item = _inventory_reference_from_data(raw_item)
            if item is not None:
                references.append(item)

    characters = root / "characters"
    for character_path in sorted(characters.glob("*.json")):
        try:
            raw_character = json.loads(character_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw_character, dict):
            continue
        raw_inventory = raw_character.get("inventory", [])
        if not isinstance(raw_inventory, list):
            continue
        for raw_item in raw_inventory:
            item = _inventory_reference_from_data(raw_item)
            if item is not None:
                references.append(item)
    return tuple(references)


def _inventory_reference_from_data(data: object) -> InventoryItem | None:
    if not isinstance(data, dict):
        return None
    try:
        return InventoryItem.from_dict({**data, "quantity": 1})
    except (KeyError, TypeError, ValueError):
        return None
