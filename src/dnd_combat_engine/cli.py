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
    subparsers.add_parser("list-campaigns", help="List known campaign ids")
    subparsers.add_parser("list-spells", help="List known spell ids")
    subparsers.add_parser("list-monsters", help="List known monster ids")
    campaign = subparsers.add_parser("campaign", help="Inspect or update a campaign")
    campaign_subparsers = campaign.add_subparsers(dest="campaign_command", required=True)
    campaign_show = campaign_subparsers.add_parser("show", help="Show campaign details")
    campaign_show.add_argument("campaign_id")
    campaign_activate = campaign_subparsers.add_parser("activate", help="Activate a campaign")
    campaign_activate.add_argument("campaign_id")
    subparsers.add_parser("gui", help="Launch the PySide6 GUI")
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
    if args.command == "list-campaigns":
        for campaign_id in app.campaigns.list_ids():
            print(campaign_id)
        return 0
    if args.command == "campaign":
        return _campaign(app, args.campaign_command, args.campaign_id)
    if args.command == "quick-attack":
        return _quick_attack(app)
    if args.command == "gui":
        from dnd_combat_engine.gui import run_gui

        return run_gui(Path(args.data_root))
    raise ValueError(f"unsupported command: {args.command}")


def _campaign(app, command: str, campaign_id: str) -> int:
    campaign = app.campaigns.load(campaign_id)
    if command == "show":
        print(f"{campaign.name} [{campaign.status.value}]")
        print(f"Characters: {', '.join(campaign.character_ids) or 'none'}")
        print(f"Encounters: {', '.join(campaign.encounter_ids) or 'none'}")
        if campaign.notes:
            print(f"Notes: {campaign.notes}")
        return 0
    if command == "activate":
        campaign = app.campaigns.activate(campaign)
        app.campaigns.save(campaign)
        print(f"{campaign.name} [{campaign.status.value}]")
        return 0
    raise ValueError(f"unsupported campaign command: {command}")


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
