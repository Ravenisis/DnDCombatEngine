"""Spell business operations."""

from __future__ import annotations

from collections.abc import Iterable

from dnd_combat_engine.models.effects import EffectKind
from dnd_combat_engine.models.spells import Spell


class SpellService:
    """Query and organize spell definitions."""

    def by_level(self, spells: Iterable[Spell], level: int) -> tuple[Spell, ...]:
        """Return spells matching a level sorted by name."""
        if not 0 <= level <= 9:
            raise ValueError("spell level must be between 0 and 9")
        return tuple(
            sorted((spell for spell in spells if spell.level == level), key=_spell_name_key)
        )

    def concentration_spells(self, spells: Iterable[Spell]) -> tuple[Spell, ...]:
        """Return concentration spells sorted by name."""
        return tuple(
            sorted((spell for spell in spells if spell.concentration), key=_spell_name_key)
        )

    def damaging_spells(self, spells: Iterable[Spell]) -> tuple[Spell, ...]:
        """Return spells that have a damage profile sorted by name."""
        return tuple(
            sorted(
                (spell for spell in spells if _has_damage_effect(spell)),
                key=_spell_name_key,
            )
        )


def _spell_name_key(spell: Spell) -> tuple[str, str]:
    return (spell.name.lower(), spell.spell_id)


def _has_damage_effect(spell: Spell) -> bool:
    if spell.damage is not None:
        return True
    return any(effect.effect_kind == EffectKind.DAMAGE for effect in spell.effects)
