"""Class-resource inference for imported and legacy character saves."""

from __future__ import annotations

import re

from dnd_combat_engine.models.character import Character
from dnd_combat_engine.models.resources import ResourcePool

CHANNEL_DIVINITY_RESOURCE = "channel_divinity"


def ensure_channel_divinity_resource(character: Character) -> bool:
    """Add or upgrade Channel Divinity uses for a character that has the feature."""
    maximum = inferred_channel_divinity_uses(character)
    if maximum == 0:
        return False
    resource = character.resources.get(CHANNEL_DIVINITY_RESOURCE)
    if resource is None:
        character.resources[CHANNEL_DIVINITY_RESOURCE] = ResourcePool(
            CHANNEL_DIVINITY_RESOURCE,
            maximum,
            maximum,
        )
        return True
    if resource.maximum >= maximum:
        return False
    spent = max(resource.maximum - resource.current, 0)
    resource.maximum = maximum
    resource.current = max(maximum - spent, 0)
    return True


def inferred_channel_divinity_uses(character: Character) -> int:
    """Infer Channel Divinity uses from class level and imported feature names."""
    text = " ".join((character.character_class, *character.features)).casefold()
    if "channel divinity" not in text:
        return 0
    class_level = _class_level(character.character_class) or character.level
    if re.search(r"\bcleric\b", text):
        return 2 if class_level >= 6 else 1
    if re.search(r"\bpaladin\b", text):
        return 1
    return 1


def _class_level(value: str) -> int | None:
    match = re.search(r"\b(\d{1,2})\b", value)
    return int(match.group(1)) if match else None
