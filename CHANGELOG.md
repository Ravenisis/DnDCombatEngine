# DnDCombatEngine Changelog

This changelog keeps tester-facing release notes and milestone patch history.
For architecture, build, and packaging details, see [DEVNOTES.md](DEVNOTES.md).

## Unreleased

### Added

- Added a mypy type-checking baseline for the extracted GUI feature modules and
  action/state boundaries.
- Added focused campaign, targeting, inventory, spellbook, and combat-panel GUI
  modules to keep feature ownership outside the main window.
- Added a regression check that exercises the live quick-attack panel path.

### Changed

- Added mypy to the development dependencies, CI matrix, developer notes, and
  release test plan.
- Strengthened annotations in the extracted campaign, inventory, spellbook,
  and targeting GUI modules.
- Added a Core Session Reliability Gate to the release test plan: automated
  checks, clean-profile startup/persistence, and a documented manual session
  pass are required before new gameplay content resumes.

## 1.0.3 - 2026-07-11

### Added

- Expanded the SRD inventory catalog from 209 to 628 selectable entries.
- Added more mundane adventuring gear, trade goods, higher-level spell scrolls,
  potion variants, magic armor, magic weapons, rings, rods, staves, wands, and
  wondrous items.
- Added more SRD treasure inventory, including gemstones, art objects, manuals,
  tomes, cursed items, bard instruments, utility wearables, and named wondrous
  loot.
- Added another SRD inventory pass with force items, elemental command items,
  figurines of wondrous power, horns, pipes, talismans, prayer beads, gauntlets,
  goggles, animated shields, special armor, special weapons, poison variants,
  and higher healing potions.
- Added richer inventory tags for magic items, attunement, bonuses, trade goods,
  scroll levels, and item behavior notes used by add-item tooltips.
- Added 23 inventory SVG icons for SRD item families such as rings, rods, wands,
  staves, magic armor, magic weapons, magic containers, gems, art objects,
  amulets, manuals, tomes, cursed loot, and wearable magic items.
- Added 6 more inventory SVG icons for figurines, force items, gauntlets,
  goggles, magic horns, and talismans.
- Added data-driven spell/action interaction metadata for the resolver and GUI
  action flow.
- Added stronger D&D Beyond PDF and URL character-import fixtures for standard
  and machine-readable sheets.
- Added a separate hosted-campaign backend boundary for future multiplayer
  hosting, joining, leaving, and closing sessions.

### Changed

- Improved inventory icon fallback tags for magic items, rings, rods, wands,
  focus items, clothing, trade goods, light sources, weapons, gems, art objects,
  books, jewelry, and cursed loot.
- Assigned the expanded SRD catalog to item-family icons so every selectable
  inventory item resolves to a concrete icon in the inventory window.
- Extended icon family matching for summoning figurines, force cubes, elemental
  command items, gauntlets, goggles, horns, and talismans.
- Improved character import extraction for names, proficiencies, resistances,
  inventory entries, quantities, currency, and D&D Beyond sheet links.

## 1.0.2 - 2026-07-10

### Added

- Added SRD-backed inventory item choices to the Add Item dialog.
- Added mouseover tooltips for SRD inventory choices with category, weight,
  purchase price, sell price, and notes.

### Fixed

- Repaired spell-slot display and casting for imported or legacy characters
  whose saves were missing spell-slot resource pools.
- Expanded the Spellbook to show every castable level from a spell's base level
  through the character's highest available spell slot.
- Filtered noisy D&D Beyond attack-table fragments such as `instead` and
  `Range` from imported attack buttons.

## 1.0.1 - 2026-07-10

### Added

- Added manual inventory item entry with autosave and immediate inventory refresh.
- Added right-side Spellbook tabs for Spells, Abilities, Cantrips, Attacks, and
  Channel Divinity.

### Fixed

- Repaired spell slot availability for legacy or incomplete character saves by
  upgrading inferred slot maps without resetting already-spent slots.
- Ensured Spellbook rank choices repair inferred spell slots before listing
  available casting levels.

## 1.0.0-beta.1 - 2026-07-10

### Release

- Marked the first public beta release as `1.0.0-beta.1`.
- Bumped the Python package version to `1.0.0b1`.
- Bumped the Windows executable, Inno installer, and MSI release version to
  `1.0.0`.
- Added release packaging support for GitHub Releases on `v*` tags.

### Fixed

- Fixed Help > Report Bug by removing a dialog helper collision and validating
  required summary/description fields before accepting the report.

### Documentation

- Split tester-facing release history out of `DEVNOTES.md` into this dedicated
  changelog.
- Kept `DEVNOTES.md` focused on development, architecture, and packaging notes.
- Added a beta tester bug-report path through the Help menu and documented
  token-backed submission options for restricted GitHub issue access.
- Added generated SRD support catalogs for spells through spell level 5, class
  and subclass abilities through character level 10, and SRD species traits.

### In Progress

- Began the hosted campaign milestone with JSON-backed hosted session models,
  join-code lifecycle operations, player roles, connected-player tracking, and
  campaign hosting documentation.

## Patch History

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
- Added dockable GUI shell with character sheet, combat log, dice tray,
  encounter, initiative, attack, menus, and status bar.
- Added pure GUI panel/table helpers plus GUI action metadata, preferences, and
  controller-backed command dispatch.
- Added CLI support for launching the GUI and tests that keep GUI logic
  verifiable without requiring PySide6 at test time.

### Begin milestone 4 campaign management

- Added campaign domain models, status lifecycle, and JSON serialization.
- Added campaign persistence, service operations, controller workflows, app
  wiring, and summary view models.
- Added starter campaign seed data and tests across models, services,
  controllers, persistence, app wiring, and seed loading.

### Expand milestone 4 campaign workspace

- Added campaign GUI panel rows, a dockable campaign widget, and campaign menu
  actions.
- Added GUI campaign commands for loading and activating the starter campaign.
- Added CLI campaign commands for listing, showing, and activating campaigns.
- Added a second seed character and encounter, then linked both into the starter
  campaign.

### Begin milestone 5 packaging and installer foundation

- Added install-safe runtime data path helpers with bundled seed data and
  writable user data initialization.
- Added `python -m dnd_combat_engine`, a GUI executable entry point, and CLI
  polish for data initialization and missing GUI dependencies.
- Added package-data configuration so JSON seed data is included in installed
  wheels and executable builds.
- Added a PyInstaller spec and Windows build script for producing
  `dist/DnDCombatEngine/DnDCombatEngine.exe`.

### Complete milestone 5 installer and release automation

- Added an Inno Setup installer script that installs the executable, registers
  uninstall support, and can create Start Menu and desktop shortcuts.
- Added a Windows installer build script that compiles
  `DnDCombatEngine-0.1.2-Setup.exe` from the PyInstaller output.
- Added a GitHub Actions packaging workflow for linting, testing, building
  Python distributions, producing the Windows executable, and uploading
  installer artifacts.
- Added release checklist documentation for local verification and GitHub
  Actions artifact publishing.

### Begin milestone 6 richer campaign and encounter editing

- Added controller-backed GUI editor helpers for campaign references and
  encounter participants.
- Added campaign and encounter editor docks with inputs, action buttons, and log
  output.
- Added campaign reference and encounter participant panel rows for richer
  desktop display.
- Expanded tests across GUI editor helpers, panel rows, and controller edit
  methods.

### Verify Windows executable and installer build

- Ran the full PyInstaller build and produced
  `dist/DnDCombatEngine/DnDCombatEngine.exe`.
- Installed Inno Setup locally with `winget` and compiled
  `dist/installer/DnDCombatEngine-0.1.2-Setup.exe`.
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

### Add MSI installer packaging

- Added WiX Toolset MSI authoring for installing the complete PyInstaller
  application folder under Program Files.
- Added an MSI build script that harvests the full packaged runtime, Qt support
  files, bundled seed data, and executable into `DnDCombatEngine-0.1.2-x64.msi`.
- Added GitHub Actions packaging support for building and uploading the MSI
  artifact.
- Documented the local MSI build workflow and expanded packaging tests.

### Add PDF character sheet import

- Added a PDF character import service for text and fillable PDF sheets using
  extracted sheet fields and text.
- Added a reviewable character import draft model and controller workflow that
  saves the imported character and links it to a selected campaign.
- Added a GUI campaign editor action for importing a character PDF into the
  active campaign.
- Added parser, controller, app wiring, and GUI helper tests for the import flow.

### Add URL character sheet import

- Added public URL import for PDF, HTML, and text character sheets through the
  character import service.
- Added controller and GUI helper workflows that save URL-imported characters and
  link them to a campaign.
- Added Campaign menu entries under `Upload Character Sheet` with `PDF` and
  `URL` submenu options.
- Added URL parser, controller, GUI helper, and menu tests.

### Fix character sheet import actions

- Connected Campaign menu import actions to working PDF file and URL prompts.
- Updated campaign editor import buttons to prompt for a PDF or URL when the
  matching input field is blank.
- Added regression tests for menu-triggered imports and dock import button
  prompt behavior.

### Add action bar UI foundation

- Removed character sheet upload controls from the Campaign Editor dock so import
  remains available from the Campaign menu only.
- Added Spellbook and Abilities dock windows for placing spells and abilities on
  a shared quick action bar.
- Added a centered bottom action bar with mouse-click activation and keyboard
  hotkeys for slots 1-0, -, and =.
- Added action bar rank update behavior so highest-rank buttons update when a new
  rank is learned while downranked or inactive-spec buttons stay unchanged.

### Refresh combat workspace installer build

- Updated the central GUI workspace label to display `Combat Workspace`.
- Rebuilt the PyInstaller executable, Inno Setup installer, and WiX MSI with the
  refreshed GUI text.
- Verified linting, tests, and packaged executable startup after the installer
  refresh.

### Add action bar combat workspace activation

- Changed the central GUI workspace into a read-only combat log for action bar
  roll output.
- Added Shift+click action bar d20 rolls into the combat workspace.
- Added normal-click action bar spell and ability activation, including spell
  damage dice rolls, slot spending, and remaining slot reporting.
- Rebuilt the PyInstaller executable, Inno Setup installer, and WiX MSI with the
  refreshed action bar behavior.

### Add keyboard shortcuts and streamline campaign UI

- Added default menu shortcuts for Spellbook (`K`), Inventory (`B`), and
  Abilities (`N`), while preserving action bar hotkeys `1` through `=`.
- Added Settings and Help menus, including key-bind reference and color scheme
  preference windows.
- Temporarily hid the Character Sheet, Dice Tray, and Encounter Editor panels
  from the startup layout.
- Changed the Campaign Editor party-member field to a dropdown of current
  campaign characters for removal.
- Updated party member right-click sheet replacement to offer PDF and URL choices
  while overwriting the selected character instead of adding a new one.

### Add utility spell workflows and inventory icons

- Added Character menu inventory access with RPG-style container sections, item
  SVG icons, quantity overlays, and right-click consumable use.
- Added spell-specific action bar workflows for Bless, Cure Wounds, Lesser
  Restoration, Light, Revivify, Thaumaturgy, and Beacon of Hope.
- Added concentration-backed party frame buff icons for Beacon of Hope and Bless.
- Improved D&D Beyond PDF imports by reading literal PDF values, sending URL
  imports through the editable review dialog, and preserving parsed inventory.
- Bumped the package, installer, and MSI version to `0.1.2`.

### Add MMORPG-style inventory currency and action controls

- Added normalized PP/GP/SP/CP character currency with editable inventory purse
  boxes and a Deposit/Withdraw ledger input.
- Updated inventory consumable use so right-clicked stacks refresh immediately
  and item tooltips show sell price when purchase price data is available.
- Added saving throw buttons beside the action bar, graphical spell slot
  tracking, working Dice menu d20 rolls, and weapon/unarmed attack options in the
  spellbook action source.
- Added Guiding Bolt spell data and refreshed the Ravenisis seed sheet with
  cleric saving throw proficiencies and prepared spell metadata.

### Refine import review and popup controls

- Changed inventory currency controls to a compact 2x2 PP/GP/SP/CP layout.
- Added toggle behavior for shortcut-opened popups so Spellbook, Abilities,
  Inventory, Key Binds, and Preferences close when their command is used again.
- Tightened character sheet skill parsing to recognize valid D&D skill names and
  ignore adjacent D&D Beyond footer/status text.
- Added import support for sheet currency totals such as `2,989GP`, carrying the
  parsed purse through the confirmation popup into the saved character.

### Next milestone: MMORPG Campaign Controller

- Build active target frames for party members, monsters, and encounter
  participants.
- Add target-aware action resolution for attacks, spells, healing, saves, buffs,
  conditions, concentration, and resource costs.
- Add combat-workspace feedback that behaves like an MMORPG controller: select a
  target, press an action bar key, resolve the effect, then update frames, logs,
  spell slots, conditions, and inventory immediately.

### Begin MMORPG Campaign Controller

- Added campaign-persisted activity entries for imports, rests, inventory use,
  money changes, and action bar resolutions.
- Added an Activity panel to the GUI so campaign history is visible in the main
  controller workspace.
- Improved active target frames with HP-aware labels and selected-target
  highlighting for party members and encounter monsters.
- Added encounter-specific monster HP tracking so selected monster targets can
  take persistent damage from action bar attacks.
- Added active-target healing and utility spell routing for Cure Wounds, Lesser
  Restoration, Light, and Revivify.
- Added visible party-frame condition summaries and an inventory Money Log popup
  for session currency changes.
- Fixed imported spellcasters losing spell slots by inferring spell slots and hit
  dice from imported caster class and level, then preserving those resources when
  saving the character.
- Bumped the package, installer, and MSI version to `0.1.2`.

### Add player-facing documentation

- Renamed the original developer-oriented README content to `DEVNOTES.md` so
  build, architecture, release, and patch-note history remain available.
- Added a new player/DM-oriented `README.md` focused on launching the app,
  importing characters, selecting targets, using the action bar, and running
  combat.
- Added user documentation for the general app flow, DM workflow, action bar,
  character sheet imports, and release test planning.
