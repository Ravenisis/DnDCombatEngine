"""Combat controller workflows."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dnd_combat_engine.engine.attacks import AttackRequest, AttackResult
from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.equipment import Weapon
from dnd_combat_engine.services.combat_service import CombatService


@dataclass(frozen=True, slots=True)
class CombatController:
    """UI-facing combat workflow coordinator."""

    combat_service: CombatService

    def attack_with_weapon(
        self,
        attacker: Character,
        target: Character,
        weapon: Weapon,
        target_armor_class: int,
        attack_bonus: int = 0,
        damage_bonus: int = 0,
        active_features: tuple[str, ...] = (),
        rng: random.Random | None = None,
    ) -> AttackResult:
        """Build and resolve a weapon attack request."""
        request = AttackRequest(
            attacker=attacker,
            target=target,
            weapon=weapon,
            target_armor_class=target_armor_class,
            attack_bonus=attack_bonus,
            damage_bonus=damage_bonus,
            active_features=active_features,
        )
        return self.combat_service.resolve_attack(request, rng=rng)

