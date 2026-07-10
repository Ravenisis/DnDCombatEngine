"""Spell slot inference helpers for imported and legacy character saves."""

from __future__ import annotations

import re

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.resources import ResourcePool


def ensure_spell_slot_resources(character: Character) -> bool:
    """Add missing spell slot resources inferred from class-like sheet text."""
    return _ensure_spell_slots(character, inferred_spell_slots(character))


def ensure_spell_slot_resources_for_level(character: Character, slot_level: int) -> bool:
    """Add spell slot resources needed to support an explicit casting level."""
    if slot_level < 1:
        return False
    slots = inferred_spell_slots(character)
    if not slots:
        minimum_level = _minimum_full_caster_level_for_slot(slot_level)
        if slot_level == 1 or character.level < minimum_level:
            return False
        slots = _full_caster_spell_slots(character.level)
    if max(slots, default=0) < slot_level:
        effective_level = max(
            character.level,
            _minimum_full_caster_level_for_slot(slot_level),
        )
        slots = _full_caster_spell_slots(effective_level)
    return _ensure_spell_slots(character, slots)


def _ensure_spell_slots(character: Character, slots: dict[int, int]) -> bool:
    changed = False
    for slot_level, maximum in slots.items():
        name = f"spell_slot_{slot_level}"
        resource = character.resources.get(name)
        if resource is None:
            character.resources[name] = ResourcePool(name, maximum, maximum)
            changed = True
            continue
        if resource.maximum < maximum:
            spent = max(resource.maximum - resource.current, 0)
            resource.maximum = maximum
            resource.current = max(maximum - spent, 0)
            changed = True
    return changed


def inferred_spell_slots(character: Character) -> dict[int, int]:
    """Infer spell slots from class, level, and imported feature text."""
    progression = _caster_progression(character)
    if progression is None:
        return {}
    effective_level = max(1, character.level)
    if progression == "half":
        effective_level = max(1, (character.level + 1) // 2)
    if progression == "third":
        effective_level = max(1, (character.level + 2) // 3)
    return _full_caster_spell_slots(effective_level)


def _caster_progression(character: Character) -> str | None:
    text = " ".join((*character.features, *character.skills)).lower()
    if re.search(r"\b(?:bard|cleric|druid|sorcerer|wizard)\b", text):
        return "full"
    if re.search(r"\b(?:paladin|ranger|artificer)\b", text):
        return "half"
    if re.search(r"\b(?:eldritch knight|arcane trickster)\b", text):
        return "third"
    if re.search(r"\b(?:cantrips?|domain spells?|spellcasting|prepared spells?)\b", text):
        return "full"
    return None


def _full_caster_spell_slots(level: int) -> dict[int, int]:
    slots_by_level = {
        1: (2,),
        2: (3,),
        3: (4, 2),
        4: (4, 3),
        5: (4, 3, 2),
        6: (4, 3, 3),
        7: (4, 3, 3, 1),
        8: (4, 3, 3, 2),
        9: (4, 3, 3, 3, 1),
        10: (4, 3, 3, 3, 2),
        11: (4, 3, 3, 3, 2, 1),
        12: (4, 3, 3, 3, 2, 1),
        13: (4, 3, 3, 3, 2, 1, 1),
        14: (4, 3, 3, 3, 2, 1, 1),
        15: (4, 3, 3, 3, 2, 1, 1, 1),
        16: (4, 3, 3, 3, 2, 1, 1, 1),
        17: (4, 3, 3, 3, 2, 1, 1, 1, 1),
        18: (4, 3, 3, 3, 3, 1, 1, 1, 1),
        19: (4, 3, 3, 3, 3, 2, 1, 1, 1),
        20: (4, 3, 3, 3, 3, 2, 2, 1, 1),
    }
    slots = slots_by_level[min(max(level, 1), 20)]
    return dict(enumerate(slots, start=1))


def _minimum_full_caster_level_for_slot(slot_level: int) -> int:
    for level in range(1, 21):
        if slot_level in _full_caster_spell_slots(level):
            return level
    return 20
