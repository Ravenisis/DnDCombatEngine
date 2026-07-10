# SRD Design Guide

This project uses the D&D 5e System Reference Document 5.2.1 as an open
licensed rules baseline for structured rules design. The repo carries the
project's SRD attribution and license reference at
[THIRD_PARTY_LICENSES/SRD.md](../THIRD_PARTY_LICENSES/SRD.md), so contributors
do not need access to any developer's local SRD checkout to understand licensing
obligations.

Any SRD-derived data or generated rules tables committed to this project must
preserve appropriate attribution, link to the license, and note meaningful
changes.

## Engineering Principles

- Treat the SRD as a rules baseline, not a pile of UI text. Convert rules into
  typed data, effect definitions, and resolution workflows.
- Keep rule edition and source version explicit. The current SRD baseline is 5.2.1
  / 2024 material, while some campaign workflows may still need 2014-compatible
  behavior.
- Prefer structured parsers over ad hoc string matching for spells, monsters,
  equipment, and character sheet imports.
- Keep player interaction fast: the GUI should ask for only the missing choices
  needed to resolve the selected action.
- Make every rule decision explainable in the Combat Workspace and activity log.

## Rules Data Model

SRD content should map into explicit models:

- `RuleSource`: source name, version, license, attribution, and page or heading
  reference when available.
- `ActionDefinition`: action, bonus action, reaction, free interaction, or
  special timing.
- `CheckDefinition`: ability check, saving throw, attack roll, DC, proficiency,
  advantage/disadvantage, and situational modifiers.
- `EffectDefinition`: damage, healing, condition application, movement, resource
  spend, resource recovery, concentration, summoned creature, or narrative effect.
- `TargetProfile`: self, one creature, multiple creatures, object, point, area,
  cone, line, sphere, cube, cylinder, or special spell-defined target.
- `DurationProfile`: instantaneous, round-based, minute/hour/day duration,
  concentration duration, until dispelled, or permanent after completion.

## Combat Resolution Workflow

The next engine layer should make every action follow the same high-level path:

1. Select actor.
2. Select action from weapons, spells, features, inventory, or custom commands.
3. Resolve required resources, timing, and concentration conflicts.
4. Select legal target or targets.
5. Determine attack roll, saving throw, ability check, or automatic effect.
6. Roll dice and apply modifiers.
7. Apply damage, healing, conditions, movement, resources, and ongoing effects.
8. Record an explainable log entry and refresh the GUI.

This workflow keeps weapons, spells, class features, monster actions, and items
on the same rails, which is important for an MMORPG-style controller.

## GUI Implications

- The active target panel should show HP, conditions, cover, range hints, and
  whether the selected action can target it.
- Action bar buttons should expose tooltips with action timing, target type,
  range, save or attack details, resource cost, duration, and source.
- Spells that need choices should open small focused prompts, not large editors.
- Conditions and concentration should be visible on party and target frames.
- Combat log entries should state what was rolled, why modifiers applied, and
  what changed.
- Rest commands should show which hit points, hit dice, spell slots, features,
  and conditions will change before applying broad recovery.

## Accuracy Backlog

High-value SRD-informed slices:

- Done: Add a `RuleSource` model and source metadata to spells, conditions,
  equipment, monsters, and parsed imports.
- Done: Add structured effect definitions, target profiles, check definitions,
  duration profiles, and a reusable resolver for target/resource/action
  validation.
- Done: Add action economy tracking per turn: action, bonus action, reaction,
  movement, object interaction, and special actions.
- Done: Add concentration lifecycle handling: start, replace, break, and save
  after damage.
- Done: Add compact SRD catalogs for spells through spell level 5, class and
  subclass abilities through level 10, and species traits for character-builder
  coverage.
- Next: Wire concentration results into dependent effect cleanup for party
  frames, target frames, and active spell buffs.
- Add SRD spell parsing/import tools that generate structured spell JSON from
  Markdown headings and spell fields.
- Add monster stat block parsing for attacks, saves, traits, senses, challenge,
  and typed damage.
- Add condition automation for advantage/disadvantage, speed changes, action
  restrictions, incapacitation, visibility, and death-state workflows.
- Add user-facing rule explanations for every automated choice.
