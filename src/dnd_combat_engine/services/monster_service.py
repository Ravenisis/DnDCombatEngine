"""Monster business operations."""

from __future__ import annotations

from collections.abc import Iterable
from fractions import Fraction

from dnd_combat_engine.models.damage import DamageType
from dnd_combat_engine.models.monsters import Monster


class MonsterService:
    """Query and inspect monster stat blocks."""

    def by_challenge_range(
        self,
        monsters: Iterable[Monster],
        minimum: Fraction | int = 0,
        maximum: Fraction | int | None = None,
    ) -> tuple[Monster, ...]:
        """Return monsters whose challenge rating falls in an inclusive range."""
        lower = Fraction(minimum)
        upper = Fraction(maximum) if maximum is not None else None
        if upper is not None and upper < lower:
            raise ValueError("maximum challenge rating cannot be below minimum")
        return tuple(
            sorted(
                (
                    monster
                    for monster in monsters
                    if monster.challenge_rating >= lower
                    and (upper is None or monster.challenge_rating <= upper)
                ),
                key=_monster_sort_key,
            )
        )

    def resistant_to(
        self,
        monsters: Iterable[Monster],
        damage_type: DamageType,
    ) -> tuple[Monster, ...]:
        """Return monsters resistant or immune to a damage type."""
        return tuple(
            sorted(
                (
                    monster
                    for monster in monsters
                    if damage_type in monster.damage_resistances
                    or damage_type in monster.damage_immunities
                ),
                key=_monster_sort_key,
            )
        )


def _monster_sort_key(monster: Monster) -> tuple[Fraction, str, str]:
    return (monster.challenge_rating, monster.name.lower(), monster.monster_id)

