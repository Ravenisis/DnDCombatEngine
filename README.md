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
persistence, and a test suite.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

## Architecture

The project keeps combat behavior event-driven. Characters and weapons are data-rich
domain objects, while services and future feature plugins decide what happens during
an attack, spell, or condition update.

