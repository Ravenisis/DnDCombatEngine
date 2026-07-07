# Import Character Sheet

DnDCombatEngine can import a character sheet into the current campaign from a
local PDF or a public sheet URL.

## Import From PDF

1. Open or create a campaign.
2. Choose Campaign > Upload Character Sheet > PDF.
3. Select the character sheet PDF.
4. Review the confirmation popup.
5. Edit any incorrect name or value fields.
6. Confirm to add the character to the campaign.

## Import From URL

1. Open or create a campaign.
2. Choose Campaign > Upload Character Sheet > URL.
3. Paste a public character sheet URL.
4. Review the confirmation popup.
5. Edit any incorrect name or value fields.
6. Confirm to add the character to the campaign.

Public D&D Beyond sheet PDF links are supported, for example:

```text
https://www.dndbeyond.com/sheet-pdfs/example_123456789.pdf
```

## Review Popup

The review popup is intentionally editable. Use it to correct:

- Character name.
- Class and level.
- HP.
- Ability scores.
- Saving throw proficiencies.
- Skills.
- Spells and attacks.
- Inventory.
- Currency.

The importer is improving over time, but PDF text extraction can be messy. The
review step protects your campaign data before it is saved.

## Updating an Existing Party Member

Right-click a party member frame and choose to upload a new character sheet. This
path replaces that party member's character data instead of adding a second copy.

Use this when a player levels up, changes prepared spells, buys equipment, or
updates HP/resources outside the app.

## What Gets Imported

The importer currently aims to read:

- Name.
- Class, level, species, and background.
- HP.
- Ability scores.
- Saving throw proficiencies.
- Skill proficiencies.
- Weapons and spell attacks.
- Prepared spells and known spell metadata.
- Inventory and storage containers.
- Currency totals.

## Common Cleanup

After importing, check:

- The character name did not include adjacent PDF labels.
- Skills are valid D&D skill names.
- Traits such as species or background did not get added as combat abilities.
- Spell slots match the character's caster class and level.
- Currency was parsed into PP, GP, SP, and CP correctly.
