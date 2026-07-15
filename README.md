# DnDCombatEngine

## Download And Install The Latest Release

1. Open the [DnDCombatEngine Releases page](https://github.com/Ravenisis/DnDCombatEngine/releases).
2. Select the release with the highest version number, then expand **Assets** if the files are hidden.
3. Download `DnDCombatEngine-<version>-x64.msi` for the standard Windows installation. The `Setup.exe` file is also available as a guided installer.
4. Open the downloaded installer, approve the Windows security prompt, and follow the installation steps.
5. Launch **DnDCombatEngine** from the Windows Start Menu or its desktop shortcut.

Do not download the automatically generated **Source code** archives unless you plan to run or build the Python project yourself.

### Which Download Should I Choose?

| Download | Best for | What it does |
| --- | --- | --- |
| `DnDCombatEngine-<version>-x64.msi` | Most Windows users | Uses the standard Windows Installer service, registers the application for repair and uninstall, and creates normal Start Menu entries. This is the recommended download. |
| `DnDCombatEngine-<version>-Setup.exe` | Users who prefer a guided setup wizard | Runs the Inno Setup installer with a familiar step-by-step interface and creates installed shortcuts and an uninstaller. |
| `DnDCombatEngine-<version>-windows.zip` | Portable use or troubleshooting | Contains the packaged application folder without installing anything. Extract the entire archive, then run `DnDCombatEngine.exe`. Windows does not create uninstall records or shortcuts automatically. |

The `.msi` and `Setup.exe` contain the same application. Install only one of them. The `.zip` must remain fully extracted because the executable depends on the bundled files beside it.

If an MSI installation completes but the application does not open, uninstall
any older **DnDCombatEngine** entry from **Settings > Apps > Installed apps**,
restart Windows if an installer reports a pending restart, and install the
latest MSI again while approving the administrator prompt. Refreshed packages
now replace same-version beta builds, and each release MSI is install-and-launch
smoke tested on a clean Windows runner.

DnDCombatEngine is a Windows desktop campaign controller for Dungeons & Dragons
combat. It is being built for the table: import characters, choose a party
leader, select targets, press action-bar buttons, track resources, and keep the
combat log moving.

The current release is an early open-source build. It already includes a PySide6
desktop interface, character import workflows, campaign and encounter panels,
spell slots, inventory, party frames, targeting, and a World of Warcraft-style
action bar.

## Get Started

1. Download or build the Windows installer.
2. Install DnDCombatEngine.
3. Launch `DnDCombatEngine` from the Start Menu or desktop shortcut.
4. Open the starter campaign, or create a new campaign from the Campaign menu.
5. Add party members by importing a character sheet PDF or URL.
6. Set a party leader from the Campaign menu.
7. Open the Spellbook or Inventory window from the Character menu.
8. Put actions on the action bar and run combat from the main workspace.

For local build and packaging notes, see [DEVNOTES.md](DEVNOTES.md). For release
history, see [CHANGELOG.md](CHANGELOG.md).

## Main Controls

- `K` toggles the party leader's Spellbook.
- `B` toggles the party leader's Inventory.
- `1` through `=` activate action-bar slots.
- Shift-click an action-bar button to roll a d20 instead of resolving the action.
- Shift-right-click an action-bar button to remove the assigned action.

Menu items show their keyboard shortcuts where available.

## Running Combat

The intended combat loop is:

1. Select or confirm the active campaign.
2. Add or import party members.
3. Set the party leader.
4. Select a target in the Target panel.
5. Press an action-bar hotkey or click an action.
6. Review the combat result in the Combat Workspace.
7. Watch HP, spell slots, concentration, inventory, and the activity log update.

See [DM Workflow](docs/dm-workflow.md) and
[Action Bar](docs/action-bar.md) for a fuller walkthrough.

## Campaign Hosting

The next major milestone is internet campaign hosting. The foundation now models
hosted campaign sessions with shareable join codes, connected players, player
roles, session status, and JSON persistence. The upcoming slices will add GUI
commands for hosting and joining, then a relay-backed lobby so other players can
connect over the internet.

See [Campaign Hosting](docs/campaign-hosting.md).

## Character Sheets

Character sheets can be imported from:

- Local PDF files.
- Public character sheet URLs, including D&D Beyond sheet PDF links.

The import confirmation window lets you review and edit fields before saving.
Existing party members can also be updated from their party-frame right-click menu.

See [Import Character Sheet](docs/import-character-sheet.md).

## Current Features

- Campaign creation, closing, party membership, party leader selection, rests,
  and campaign activity history.
- Party frames with HP, temporary HP, initiative, position, conditions, and
  concentration buff icons.
- Target selection for party members and encounter monsters.
- Action bar with spell, ability, attack, save, and quick-roll workflows.
- Spell slot tracking and rest recovery.
- Inventory window with containers, item icons, quantities, currency, money log,
  consumable use, and drag-and-drop storage.
- Equipment window with body-positioned gear slots and base-versus-equipped stat
  comparisons. Right-click a body slot to choose compatible carried gear.
- Movable Spellbook, Inventory, and Equipment windows remember their last size
  and position and can be closed with their title-bar X or Escape.
- PDF and URL character sheet import with editable confirmation.
- JSON-backed data for campaigns, characters, monsters, spells, actions, and
  encounters.
- Windows EXE, guided installer, and MSI packaging.
- Hosted-session backend snapshots and live WebSocket event broadcasts for HP,
  initiative, hit rolls, and action results.

## Documentation

- [User Guide](docs/user-guide.md)
- [DM Workflow](docs/dm-workflow.md)
- [Action Bar](docs/action-bar.md)
- [Campaign Hosting](docs/campaign-hosting.md)
- [Import Character Sheet](docs/import-character-sheet.md)
- [Release Test Plan](docs/release-test-plan.md)
- [Beta Feedback](docs/beta-feedback.md)
- [SRD Design Guide](docs/srd-design-guide.md)
- [SRD Attribution](THIRD_PARTY_LICENSES/SRD.md)
- [Changelog](CHANGELOG.md)
- [Developer Notes](DEVNOTES.md)

## Project Status

DnDCombatEngine is in public beta. The next major milestone is hosted campaign
play: a DM can host a campaign, share a join code, and bring remote players into
the same campaign controller over the internet.
