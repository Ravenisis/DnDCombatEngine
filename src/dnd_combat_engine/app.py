"""Application wiring helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dnd_combat_engine.controllers import (
    CharacterController,
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


@dataclass(frozen=True, slots=True)
class DnDCombatEngineApp:
    """Container for UI-facing controllers."""

    characters: CharacterController
    combat: CombatController
    combat_log: CombatLogController
    compendium: CompendiumController
    dice: DiceController
    encounters: EncounterController
    inventory: InventoryController


def create_app(data_root: Path | str = "data") -> DnDCombatEngineApp:
    """Create a fully wired application controller container."""
    dice_service = DiceService()
    persistence_service = PersistenceService(JsonFileStore(data_root))
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
        characters=CharacterController(CharacterService(), persistence_service),
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
    )

