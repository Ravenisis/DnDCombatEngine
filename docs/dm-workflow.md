# DM Workflow

DnDCombatEngine is moving toward an MMORPG-style campaign controller: one screen
for running the table, resolving actions, tracking state, and keeping the log
clean.

## Before the Session

1. Install or launch the latest build.
2. Create a campaign or open an existing one.
3. Import each player character from PDF or URL.
4. Review each imported character in the confirmation popup.
5. Set the party leader.
6. Open the Spellbook, Abilities, and Inventory windows to confirm the active
   character has expected actions, spells, resources, currency, and inventory.
7. Put common spells and attacks on the action bar.

## Starting an Encounter

1. Add or select an encounter.
2. Enter initiative rolls for party members from the party frame controls.
3. Confirm monster participants and quantities.
4. Select the first active target in the Target panel.
5. Keep the Combat Workspace visible.

## During Combat

Use this loop:

1. Confirm the acting character or set a new party leader.
2. Select the target.
3. Press an action-bar hotkey or click an action.
4. Let the resolver spend resources, roll dice, and apply target effects.
5. Read the result in the Combat Workspace.
6. Check party frames, monster HP, spell slots, concentration icons, and
   inventory.
7. Move to the next turn.

## Handling Spells

For spells such as Bless or Beacon of Hope, the app prompts for affected party
members and tracks the concentration-backed buff icons. When concentration is
broken, dependent icons are removed and the activity/combat log records the
change.

Healing spells such as Cure Wounds apply to selected party targets and update HP.
Utility spells write useful table text to the Combat Workspace.

## Handling Inventory

Open Inventory with `B`. Right-click consumables to consume one. Currency changes
can be recorded through the ledger, and the Money Log gives a session-friendly
record of deposits and withdrawals.

## Ending Combat

At the end of combat:

- Clear or complete the encounter.
- Confirm lingering concentration effects.
- Apply rests if appropriate.
- Review the Activity panel for a campaign history snapshot.

## What Still Needs Manual Judgment

The app is early and should assist, not replace, the DM. Confirm edge cases such
as unusual spell targeting, custom class features, improvised actions, reactions,
advantage/disadvantage sources, and house rules.
