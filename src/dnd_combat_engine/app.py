"""Application wiring helpers."""

from __future__ import annotations

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
    InitiativeService,
    InventoryService,
    MonsterService,
    PersistenceService,
    SpellService,
)
from dnd_combat_engine.utils.paths import default_data_root


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


def create_app(data_root: Path | str | None = None) -> DnDCombatEngineApp:
    """Create a fully wired application controller container."""
    resolved_data_root = Path(data_root) if data_root is not None else default_data_root()
    dice_service = DiceService()
    persistence_service = PersistenceService(JsonFileStore(resolved_data_root))
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
        inventory=InventoryController(InventoryService(), persistence_service),
        beta_reports=BetaReportController(
            BetaReportService(),
            _default_beta_report_path(resolved_data_root),
        ),
    )


def _default_beta_report_path(data_root: Path) -> Path:
    """Return the best local beta report target for the current runtime."""
    project_root = data_root.parent if data_root.name == "data" else data_root
    if (project_root / "pyproject.toml").exists():
        return project_root / "BETA_TESTER_REPORTS.md"
    return data_root / "BETA_TESTER_REPORTS.md"
