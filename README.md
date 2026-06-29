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

Or use the CLI:

```bash
dnd-combat-engine roll 4d6dl1
dnd-combat-engine quick-attack
```

Install and launch the GUI:

```bash
python -m pip install -e ".[gui]"
dnd-combat-engine gui
```

Initialize writable user data for an installed app profile:

```bash
dnd-combat-engine init-user-data
```

Build a Windows desktop executable:

```powershell
.\scripts\build_windows.ps1
```

Build a Windows installer after the executable:

```powershell
.\scripts\build_installer.ps1
```

## Architecture

The project keeps combat behavior event-driven. Characters and weapons are data-rich
domain objects, while services and future feature plugins decide what happens during
an attack, spell, or condition update.

## Current Foundation

- Domain models for campaigns, characters, hit points, damage, equipment, inventory,
  conditions, resources, spells, monsters, and encounters.
- Services for campaigns, characters, combat, dice, initiative, inventory, monsters,
  spells, encounters, and JSON persistence.
- Controllers for UI-facing campaign, character, combat, compendium, dice, encounter,
  and inventory workflows.
- Application wiring through `dnd_combat_engine.app.create_app`.
- Combat log models, service, and controller for UI display.
- PySide6 GUI shell with dockable character sheet, combat log, and dice tray.
- Campaign workspace support with campaign persistence, controller workflows, seed
  campaign data, CLI inspection, GUI campaign editing, and encounter editing docks.
- Event-driven combat feature plugins for Bless, Sneak Attack, Hunter's Mark, Hex,
  Rage, Divine Smite, Sharpshooter, and Great Weapon Master.
- Seed JSON under `data/` for starter equipment, a campaign, a character, a monster,
  spells, and an encounter.

## Release Gate

Milestone code should pass:

```bash
python -m ruff check .
python -m pytest
```

## Windows Installer

The Windows packaging path uses PyInstaller for the desktop executable and Inno
Setup for the installer.

```powershell
python -m pip install -e ".[dev,gui,installer]"
python -m ruff check .
python -m pytest
.\scripts\build_windows.ps1 -SkipInstall
.\scripts\build_installer.ps1 -SkipExecutableBuild
```

Expected outputs:

- `dist/DnDCombatEngine/DnDCombatEngine.exe`
- `dist/installer/DnDCombatEngine-0.1.0-Setup.exe`

Latest verified local build:

- `dist/DnDCombatEngine/DnDCombatEngine.exe` - 1,913,221 bytes
- `dist/installer/DnDCombatEngine-0.1.0-Setup.exe` - 33,166,876 bytes
- Verified with `python -m pytest` and `python -m ruff check .`

Latest verified local install smoke test:

- Ran `DnDCombatEngine-0.1.0-Setup.exe` silently into a controlled test install
  directory.
- Launched the installed `DnDCombatEngine.exe` from that install directory.
- Confirmed the app stayed running past startup and initialized user data under
  `%LOCALAPPDATA%\DnDCombatEngine\data`.
- Closed the launched app process after verification.

The installed application initializes writable user data automatically from the
bundled seed JSON. The same initialization can be run manually with:

```bash
dnd-combat-engine init-user-data
```

## Release Checklist

- Run `python -m ruff check .`.
- Run `python -m pytest`.
- Build Python distributions with `python -m build`.
- Build the Windows executable with `.\scripts\build_windows.ps1 -SkipInstall`.
- Build the Windows installer with `.\scripts\build_installer.ps1 -SkipExecutableBuild`.
- Confirm the installer launches `DnDCombatEngine.exe` and creates uninstall entries.
- Upload the wheel, source distribution, executable folder artifact, and installer
  artifact from the `Package` GitHub Actions workflow.

## Patch Notes

### Milestone 1 foundation

- Added project configuration, development tooling, package metadata, and GitHub
  test workflow.
- Added core domain models for abilities, hit points, damage profiles, weapons,
  armor, characters, inventory, resources, conditions, spells, monsters, and
  encounters.
- Added the dice engine with parser support for common dice notation, keep/drop
  modifiers, exploding dice, rerolls, minimums, maximums, and averages.
- Added JSON persistence, starter seed data, examples, CLI entry points, and the
  first unit test suite.

### Milestone 2 layered combat and controllers

- Added event-driven combat resolution, attack requests/results, initiative
  tracking, and combat log models.
- Added rules-engine feature plugins for Bless, Sneak Attack, Hunter's Mark, Hex,
  Rage, Divine Smite, Sharpshooter, and Great Weapon Master.
- Added service-layer workflows for characters, combat, dice, initiative,
  inventory, monsters, spells, encounters, combat logs, and persistence.
- Added UI-facing controllers and compact view models for combat, compendium,
  dice, encounters, inventory, characters, logs, and summaries.

### Milestone 3 GUI foundation

- Added optional PySide6 support, GUI dependency handling, dark theme styling, and
  GUI session persistence.
- Added dockable GUI shell with character sheet, combat log, dice tray, encounter,
  initiative, attack, menus, and status bar.
- Added pure GUI panel/table helpers plus GUI action metadata, preferences, and
  controller-backed command dispatch.
- Added CLI support for launching the GUI and tests that keep GUI logic verifiable
  without requiring PySide6 at test time.

### Begin milestone 4 campaign management

- Added campaign domain models, status lifecycle, and JSON serialization.
- Added campaign persistence, service operations, controller workflows, app wiring,
  and summary view models.
- Added starter campaign seed data and tests across models, services, controllers,
  persistence, app wiring, and seed loading.

### Expand milestone 4 campaign workspace

- Added campaign GUI panel rows, a dockable campaign widget, and campaign menu
  actions.
- Added GUI campaign commands for loading and activating the starter campaign.
- Added CLI campaign commands for listing, showing, and activating campaigns.
- Added a second seed character and encounter, then linked both into the starter
  campaign.

### Begin milestone 5 packaging and installer foundation

- Added install-safe runtime data path helpers with bundled seed data and writable
  user data initialization.
- Added `python -m dnd_combat_engine`, a GUI executable entry point, and CLI polish
  for data initialization and missing GUI dependencies.
- Added package-data configuration so JSON seed data is included in installed
  wheels and executable builds.
- Added a PyInstaller spec and Windows build script for producing
  `dist/DnDCombatEngine/DnDCombatEngine.exe`.

### Complete milestone 5 installer and release automation

- Added an Inno Setup installer script that installs the executable, registers
  uninstall support, and can create Start Menu and desktop shortcuts.
- Added a Windows installer build script that compiles
  `DnDCombatEngine-0.1.0-Setup.exe` from the PyInstaller output.
- Added a GitHub Actions packaging workflow for linting, testing, building Python
  distributions, producing the Windows executable, and uploading installer
  artifacts.
- Added release checklist documentation for local verification and GitHub Actions
  artifact publishing.

### Begin milestone 6 richer campaign and encounter editing

- Added controller-backed GUI editor helpers for campaign references and encounter
  participants.
- Added campaign and encounter editor docks with inputs, action buttons, and log
  output.
- Added campaign reference and encounter participant panel rows for richer desktop
  display.
- Expanded tests across GUI editor helpers, panel rows, and controller edit methods.

### Verify Windows executable and installer build

- Ran the full PyInstaller build and produced
  `dist/DnDCombatEngine/DnDCombatEngine.exe`.
- Installed Inno Setup locally with `winget` and compiled
  `dist/installer/DnDCombatEngine-0.1.0-Setup.exe`.
- Updated the installer build script to detect Inno Setup installed under the
  current user's local programs directory.
- Re-ran the test and lint gates after the build script update.

### Verify installed app launch

- Ran the generated Inno installer end-to-end into a controlled test install
  directory.
- Launched the installed executable and confirmed it remained running after
  startup.
- Verified first-run user data initialization under the local application data
  directory.
