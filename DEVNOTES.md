# DnDCombatEngine Developer Notes

This file keeps development, architecture, and packaging notes. For player and
DM usage, start with [README.md](README.md). For release history, see
[CHANGELOG.md](CHANGELOG.md).

## Current Development Focus

The project is in a reliability pass. Do not add new gameplay content until the
Core Session Reliability Gate in [docs/release-test-plan.md](docs/release-test-plan.md)
is complete: automated checks, a clean-profile startup and persistence check,
and a documented manual session pass. Capture any observed failure in a
regression test before implementing its fix.

## Current Candidate Changes

- GitHub-hosted test and package workflows use Node.js 24-backed releases of
  checkout, setup-python, and upload-artifact; Python coverage and packaging
  behavior remain unchanged.
- The Action Bar dock now exposes the party leader's initiative roll beside
  saving throws. Imported initiative modifiers feed both this control and the
  encounter initiative service, and the resulting total refreshes party order.
- Polyhedral controls have enough vertical space for their icon-and-label
  layout, with percentile notation displayed consistently as `d100`.
- The Action Bar dock includes a visual seven-piece polyhedral dice strip.
  These controls reuse the Dice menu's roll, log, status, duplicate-signal,
  and previous-die behavior instead of maintaining a separate GUI code path.
- The CI matrix installs PySide6 on every supported operating system and runs a
  real offscreen desktop smoke test as part of the coverage-enforced full suite.
- Spellbook and Inventory overlays are larger and scrollable; Campaign Activity
  is now a dedicated scrollable popup from the Campaign menu.
- Key Binds and Preferences include visible Close commands. Preferences retain
  the active color selection, and dice/save interaction paths ignore duplicate
  GUI activation signals.
- The command side of the desktop UI is organized into Campaign, Combat, and
  Manage tabs to keep workflow controls reachable without a single tall panel.
- Spellbook, Inventory, Key Binds, Preferences, and Money Log are child
  overlays within the main window, allowing window-only streaming to capture
  them alongside the Combat Workspace.
- The standalone Abilities popup and `N` shortcut were removed; abilities are
  selected from the Spellbook tab.
- Hosted campaigns have a persisted local-loopback smoke test and the first
  WebSocket lifecycle relay transport. A relay-backed desktop client and live
  action synchronization are still future slices.

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

## Rules Reference

The project can use the D&D 5e SRD as an open licensed rules baseline for future
design work. See [SRD Design Guide](docs/srd-design-guide.md) and
[SRD Attribution](THIRD_PARTY_LICENSES/SRD.md) for attribution requirements and
the planned rules-to-engine architecture.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy
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

Build a Windows MSI installer after the executable:

```powershell
.\scripts\build_msi.ps1
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
- PDF character sheet import support for creating a character draft, saving it as
  JSON, and linking the imported character to a campaign.
- URL character sheet import support for public PDF, HTML, and text sheet links,
  using the same save-and-link campaign workflow.
- Event-driven combat feature plugins for Bless, Sneak Attack, Hunter's Mark, Hex,
  Rage, Divine Smite, Sharpshooter, and Great Weapon Master.
- Seed JSON under `data/` for starter equipment, a campaign, a character, a monster,
  spells, and an encounter.

## Release Gate

Milestone code should pass:

```bash
python -m ruff check .
python -m pytest
python -m mypy
```

## Windows Installer

The Windows packaging path uses PyInstaller for the desktop executable. Inno Setup
builds a guided `.exe` installer, and WiX Toolset builds a Windows Installer
`.msi` package.

```powershell
python -m pip install -e ".[dev,gui,installer]"
python -m ruff check .
python -m pytest
.\scripts\build_windows.ps1 -SkipInstall
.\scripts\build_installer.ps1 -SkipExecutableBuild
.\scripts\build_msi.ps1 -SkipExecutableBuild
```

Expected outputs:

- `dist/DnDCombatEngine/DnDCombatEngine.exe`
- `dist/DnDCombatEngine-1.0.3-windows.zip`
- `dist/installer/DnDCombatEngine-1.0.3-Setup.exe`
- `dist/msi/DnDCombatEngine-1.0.3-x64.msi`

The MSI build requires WiX Toolset command-line tools. On a local Windows machine:

```powershell
winget install --id WiXToolset.WiXCLI --accept-package-agreements --accept-source-agreements
```

Latest verified local build:

- `dist/DnDCombatEngine/DnDCombatEngine.exe` - 4,202,962 bytes
- `dist/installer/DnDCombatEngine-1.0.3-Setup.exe` - 38,408,297 bytes
- `dist/msi/DnDCombatEngine-1.0.3-x64.msi` - 43,904,954 bytes
- Verified with `ruff`, `370` coverage-enforced tests at `90.14%`, mypy, a
  PyInstaller rebuild, an Inno Setup rebuild, and a WiX MSI rebuild.

Latest verified local install smoke test:

- The installer smoke-test workflow has previously been verified with a silent
  install into a controlled test directory, installed app launch, startup
  stability check, and user data initialization under
  `%LOCALAPPDATA%\DnDCombatEngine\data`.
- The rebuilt `1.0.3` executable, Inno installer, and MSI were produced locally.
  The Inno installer was then synchronized to `C:\Program Files\DnDCombatEngine`;
  its installed executable matched the distribution SHA-256 and passed a hidden
  startup smoke test.

The installed application initializes writable user data automatically from the
bundled seed JSON. The same initialization can be run manually with:

```bash
dnd-combat-engine init-user-data
```

## Release Checklist

- Run `python -m ruff check .`.
- Run `python -m pytest`.
- Run `python -m mypy`.
- Build Python distributions with `python -m build`.
- Build the Windows executable with `.\scripts\build_windows.ps1 -SkipInstall`.
- Build the Windows installer with `.\scripts\build_installer.ps1 -SkipExecutableBuild`.
- Build the Windows MSI with `.\scripts\build_msi.ps1 -SkipExecutableBuild`.
- Confirm the installer launches `DnDCombatEngine.exe` and creates uninstall entries.
- Upload the wheel, source distribution, zipped executable folder, installer,
  and MSI artifacts from the `Package` GitHub Actions workflow.

## Release History

Tester-facing release notes and milestone patch history live in
[CHANGELOG.md](CHANGELOG.md).
