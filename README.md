# DnDCombatEngine

A professional, open-source Dungeons & Dragons combat engine built in layers:

```text
GUI
Controllers
Rules Engine
Combat Engine
Models
Persistence
Utilities
```

Milestone 1 establishes the foundation: domain models, a dice parser and roller, JSON
persistence, seed data, and a test suite.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

Run the sample attack:

```bash
python examples/quick_attack.py
```

## Architecture

The project keeps combat behavior event-driven. Characters and weapons are data-rich
domain objects, while services and future feature plugins decide what happens during
an attack, spell, or condition update.

## Current Foundation

- Domain models for characters, hit points, damage, equipment, inventory, conditions,
  resources, spells, monsters, and encounters.
- Services for characters, combat, dice, initiative, inventory, monsters, spells,
  encounters, and JSON persistence.
- Controllers for UI-facing character, combat, compendium, dice, encounter, and
  inventory workflows.
- Application wiring through `dnd_combat_engine.app.create_app`.
- Combat log models, service, and controller for UI display.
- Event-driven combat feature plugins for Bless, Sneak Attack, Hunter's Mark, Hex,
  Rage, Divine Smite, Sharpshooter, and Great Weapon Master.
- Seed JSON under `data/` for starter equipment, a character, a monster, spells, and
  an encounter.

## Release Gate

Milestone code should pass:

```bash
python -m ruff check .
python -m pytest
```
