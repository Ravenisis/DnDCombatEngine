# Action Bar

The action bar is the primary in-combat control surface. It is designed to behave
like an MMORPG hotbar for tabletop combat.

## Slots and Hotkeys

The action bar supports twelve quick slots:

- `1`
- `2`
- `3`
- `4`
- `5`
- `6`
- `7`
- `8`
- `9`
- `0`
- `-`
- `=`

Click a slot or press its hotkey to activate the assigned action.

## Adding Actions

Open the party leader's Spellbook with `K`. Its tabs include spells, cantrips,
attacks, channel divinity, and abilities that can be placed onto the action bar.

Spellbook entries include available spell levels so downranked or upranked
casting can be represented as distinct buttons where the sheet supports it.

## Removing Actions

Shift-right-click an action-bar button to remove the assigned spell or ability.

## Quick d20 Roll

Shift-click an action-bar button to roll `1d20` into the Combat Workspace without
resolving the assigned action. This is useful for quick checks, improvised
rolls, and table rulings.

## Spell Slots

Spell slots appear to the left of the action bar as graphical slot indicators.
When a spell spends a slot, the app updates the tracker and reports the remaining
slots in the Combat Workspace.

Long rests restore spell slots. Short rest behavior depends on the character and
resource type.

## Targeted Actions

When a target is selected, action-bar attacks and spells can apply results to
that target:

- Damage reduces tracked HP.
- Healing restores party member HP.
- Buffs and concentration effects display on party frames.
- Utility effects write table-facing results to the Combat Workspace.

If no target is selected, the app may prompt for a target or hold the action.

## Rank Updates

When the character learns a new highest rank of a spell or ability, buttons that
were using the previous highest rank can update to the new highest rank. Buttons
that intentionally use a downranked version should remain downranked.

## Design Goal

The long-term goal is one dependable action loop:

1. Actor selected.
2. Action selected.
3. Resource and action economy checked.
4. Legal targets selected.
5. Dice rolled.
6. Damage, healing, buffs, conditions, inventory, and concentration resolved.
7. Combat Workspace and campaign activity log updated.
8. State persisted.
