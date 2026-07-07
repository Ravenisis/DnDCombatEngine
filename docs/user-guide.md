# User Guide

This guide is for players and Dungeon Masters who want to use DnDCombatEngine as
a campaign control panel during play.

## Launch the App

Install the Windows build, then start `DnDCombatEngine` from the Start Menu or
desktop shortcut. The app opens to a dark desktop workspace with campaign tools
on the left, the Combat Workspace on the right, and the action bar along the
bottom.

If you are running from source, use:

```powershell
dnd-combat-engine gui
```

## Open or Create a Campaign

Use the Campaign menu to:

- Open the starter campaign.
- Begin a new campaign.
- Close the current campaign.
- Add a party member.
- Set the party leader.
- Import character sheets.
- Take a short rest or long rest.

The active campaign controls which characters appear in the party frame, which
encounter data is available, and where activity is recorded.

## Party Leader

The party leader is the active character for Spellbook, Abilities, Inventory,
saving throws, and action-bar casting. Set the party leader from the Campaign
menu after adding party members.

## Party Frames

Party frames show each player character's:

- Name.
- Current and maximum HP.
- Temporary HP.
- Initiative and position.
- Active conditions.
- Concentration-based buff icons.

Right-click a party member to remove them, update their sheet from PDF or URL, or
enter initiative information.

## Targeting

Use the Target panel to select a party member or encounter monster. Once a target
is selected, action-bar spells and attacks can apply damage, healing, buffs, or
other effects to that target.

If an action needs a specific target and none is selected, the app prompts for
one when possible.

## Spellbook, Abilities, and Inventory

Open these windows from the Character menu:

- Spellbook: spells and spell-like attacks for the party leader.
- Abilities: configured combat abilities and weapon attacks.
- Inventory: carried items, storage containers, currency, and consumables.

Default shortcuts:

- `K`: Spellbook.
- `N`: Abilities.
- `B`: Inventory.

Pressing the shortcut again closes the same popup.

## Combat Workspace

The Combat Workspace is the running play log. It records:

- Action-bar activations.
- Damage and healing rolls.
- Saving throws.
- Spell slot use.
- Inventory consumable use.
- Rest and campaign activity messages.
- Concentration changes.

Use it as the table-facing history of what just happened.

## Rests

Use Campaign > Rest > Short Rest or Campaign > Rest > Long Rest.

Short rest and long rest behavior is still being refined, but the goal is:

- Short rest restores short-rest resources where applicable.
- Long rest heals characters and resets spell slots and long-rest resources.

## Inventory and Currency

The Inventory window groups items by container and shows item icons, quantities,
tooltips, and currency. Enter currency in the ledger field using text such as:

```text
1PP 100GP 25SP 9CP
```

Use Deposit to add currency and Withdraw to spend it. The purse normalizes money
using:

- 1 PP = 10 GP.
- 1 GP = 10 SP.
- 1 SP = 10 CP.

Right-click consumables to use one. Healing potions roll and report their healing
in the Combat Workspace.
