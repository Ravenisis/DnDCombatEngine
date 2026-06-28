"""Run a tiny attack example from seed data."""

from __future__ import annotations

import random
from pathlib import Path

from dnd_combat_engine.app import create_app
from dnd_combat_engine.models import CombatLog


def main() -> None:
    """Resolve a sample attack and print a combat log line."""
    app = create_app(Path(__file__).resolve().parents[1] / "data")
    attacker = app.characters.load("vale")
    target = app.compendium.load_monster("goblin")
    target_character = attacker.__class__(
        character_id=target.monster_id,
        name=target.name,
        hit_points=target.hit_points,
        abilities=target.abilities,
    )
    result = app.combat.attack_with_weapon(
        attacker=attacker,
        target=target_character,
        weapon=attacker.weapons[0],
        target_armor_class=target.armor_class,
        attack_bonus=5,
        active_features=("Sneak Attack",),
        rng=random.Random(7),
    )
    log = app.combat_log.record_attack(CombatLog(), result)
    print(log.entries[-1].message)
    print(f"{target_character.name} HP: {target_character.hit_points.current}")


if __name__ == "__main__":
    main()

