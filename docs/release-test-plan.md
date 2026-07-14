# Release Test Plan

Use this checklist before publishing a new build or installer.

## Source Checks

Run:

```powershell
python -m ruff check .
python -m pytest --cov-fail-under=90 --basetemp .\tmp\pytest
python -m mypy
```

If local coverage is below the configured release gate, note the exact coverage
result and decide whether the release is a development preview or a gated
release.

## Core Session Reliability Gate

Do not begin or merge new gameplay content until this gate is complete:

- `ruff`, `pytest`, coverage, and mypy pass on the candidate worktree.
- A clean user-data profile initializes seed data, persists a campaign change,
  and starts the packaged executable successfully.
- A tester completes the Import, GUI, Combat, Inventory, and Rest smoke tests
  below in one session without a crash, lost save, or incorrect action result.
- Any failure observed during that session is captured as a regression test
  before its fix is implemented.

Record the build version, tester, date, and any known limitations with the
release notes. A passing automated run alone does not clear this gate.

## Import Smoke Tests

Test both import paths:

- Import a local PDF into a new campaign.
- Import a public character sheet URL into the same campaign.
- Confirm the review popup appears.
- Confirm edited values are saved.
- Confirm an existing party member can be updated from the party frame menu
  without adding a duplicate party member.

## GUI Smoke Tests

Launch the app and verify:

- Campaign menu opens.
- Character menu opens Spellbook and Inventory.
- `K` and `B` toggle their windows open and closed.
- Share only the DnDCombatEngine window and confirm Spellbook and Inventory
  remain visible in the stream as embedded overlays.
- Target panel can select a party member or monster.
- Action bar hotkeys `1` through `=` activate slots.
- Shift-click on an action-bar slot rolls a d20.
- Shift-right-click removes an action-bar assignment.
- Dice menu d20 command rolls into the Combat Workspace.

## Combat Smoke Tests

Run a starter combat:

1. Open the starter campaign.
2. Set Ravenisis as party leader.
3. Select a monster target.
4. Place a weapon attack and Guiding Bolt on the action bar.
5. Activate both actions and confirm damage appears in the Combat Workspace.
6. Select a party member target.
7. Cast Cure Wounds and confirm HP changes.
8. Cast Bless or Beacon of Hope and confirm party-frame buff icons appear.
9. Break concentration and confirm dependent icons are removed.

## Inventory Smoke Tests

Open Inventory and verify:

- Containers are separated visually.
- Item icons render.
- Quantity overlays update after consumable use.
- Tooltips include item information and sell price where available.
- Currency Deposit and Withdraw normalize PP, GP, SP, and CP.
- Money Log opens and records currency activity.

## Rest Smoke Tests

Use Campaign > Rest:

- Short Rest.
- Long Rest.

Confirm HP, hit dice, spell slots, and resources update according to current app
rules.

## Packaging Checks

Build:

```powershell
.\scripts\build_windows.ps1 -SkipInstall
.\scripts\build_installer.ps1 -SkipExecutableBuild
.\scripts\build_msi.ps1 -SkipExecutableBuild
```

Expected outputs:

- `dist/DnDCombatEngine/DnDCombatEngine.exe`
- `dist/installer/DnDCombatEngine-1.0.3-Setup.exe`
- `dist/msi/DnDCombatEngine-1.0.3-x64.msi`

## Installer Smoke Test

Install the app into a clean test directory or test machine.

Verify:

- Start Menu shortcut is created.
- Desktop shortcut is created when selected.
- App launches.
- App icon appears.
- Bundled seed data initializes under the user data directory.
- Uninstall entry exists.
- Uninstall removes the installed app files.

## Release Notes

Before upload:

- Update `CHANGELOG.md` with tester-facing patch notes.
- Confirm `README.md` still reflects user-facing behavior.
- Confirm docs are current.
- Bump package and installer version when appropriate.
