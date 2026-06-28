# Contributing

Thanks for helping build DnDCombatEngine.

## Local Checks

Run these before opening a pull request:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest
```

The test suite enforces at least 90% coverage.

## Architecture Rules

The project is layered:

```text
GUI
Controllers
Rules Engine
Combat Engine
Models
Persistence
Utilities
```

Each layer should only call the layer beneath it. Domain models should stay focused on
data and validation. Business workflows belong in services. Class features, spell
effects, feats, and conditions should be implemented as feature plugins that react to
engine events.

## Data

JSON seed data lives under `data/` and should round-trip through the public domain
models. Add or update tests when adding new schema fields.

