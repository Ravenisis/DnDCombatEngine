"""Command line interface for manual engine checks."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from dnd_combat_engine.app import create_app
from dnd_combat_engine.models import CombatLog


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="dnd-combat-engine")
    parser.add_argument("--data-root", default="data", help="Path to JSON data root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    roll = subparsers.add_parser("roll", help="Roll dice notation")
    roll.add_argument("notation")
    roll.add_argument("--seed", type=int)

    subparsers.add_parser("quick-attack", help="Run the seeded quick attack")
    subparsers.add_parser("list-spells", help="List known spell ids")
    subparsers.add_parser("list-monsters", help="List known monster ids")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    args = build_parser().parse_args(argv)
    app = create_app(Path(args.data_root))
    if args.command == "roll":
        rng = random.Random(args.seed) if args.seed is not None else None
        result = app.dice.roll(args.notation, rng=rng)
        print(f"{result.notation}: {result.total} {result.rolls}")
        return 0
    if args.command == "list-spells":
        for spell_id in app.compendium.persistence_service.list_spell_ids():
            print(spell_id)
        return 0
    if args.command == "list-monsters":
        for monster_id in app.compendium.persistence_service.list_monster_ids():
            print(monster_id)
        return 0
    if args.command == "quick-attack":
        return _quick_attack(app)
    raise ValueError(f"unsupported command: {args.command}")


def _quick_attack(app) -> int:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

