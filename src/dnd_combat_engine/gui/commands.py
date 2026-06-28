"""GUI command dispatch helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dnd_combat_engine.app import DnDCombatEngineApp
from dnd_combat_engine.controllers import (
    ControllerError,
    ControllerResult,
    capture_controller_error,
)
from dnd_combat_engine.models import Character, CombatLog


@dataclass(frozen=True, slots=True)
class GuiCommandDispatcher:
    """Dispatch declarative GUI action IDs to controller-backed commands."""

    app: DnDCombatEngineApp

    def dispatch(self, command_id: str) -> ControllerResult[str]:
        """Run a GUI command and return a UI-friendly result."""
        commands = {
            "combat.quick_attack": self._quick_attack,
            "dice.roll_d20": self._roll_d20,
            "view.reset_layout": lambda: "Layout reset.",
        }
        command = commands.get(command_id)
        if command is None:
            return ControllerResult(
                error=ControllerError("unknown_command", f"Unknown GUI command: {command_id}")
            )
        return capture_controller_error(command)

    def _roll_d20(self) -> str:
        result = self.app.dice.roll("1d20")
        return f"{result.notation}: {result.total}"

    def _quick_attack(self) -> str:
        attacker = self.app.characters.load("vale")
        monster = self.app.compendium.load_monster("goblin")
        target = Character(
            character_id=monster.monster_id,
            name=monster.name,
            hit_points=monster.hit_points,
            abilities=monster.abilities,
        )
        result = self.app.combat.attack_with_weapon(
            attacker=attacker,
            target=target,
            weapon=attacker.weapons[0],
            target_armor_class=monster.armor_class,
            attack_bonus=5,
            active_features=("Sneak Attack",),
        )
        log = self.app.combat_log.record_attack(CombatLog(), result)
        return log.entries[-1].message
