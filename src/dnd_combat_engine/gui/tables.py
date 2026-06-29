"""Pure table data helpers for GUI views."""

from __future__ import annotations

from dnd_combat_engine.models import Campaign, Monster, Spell


def campaign_table_rows(campaigns: tuple[Campaign, ...]) -> list[tuple[str, str, str, str]]:
    """Return sorted campaign rows for table widgets."""
    return [
        (
            campaign.campaign_id,
            campaign.name,
            campaign.status.value,
            str(len(campaign.encounter_ids)),
        )
        for campaign in sorted(campaigns, key=lambda campaign: campaign.name.lower())
    ]


def spell_table_rows(spells: tuple[Spell, ...]) -> list[tuple[str, str, str, str]]:
    """Return sorted spell rows for table widgets."""
    return [
        (spell.spell_id, spell.name, str(spell.level), spell.school.value)
        for spell in sorted(spells, key=lambda spell: (spell.level, spell.name.lower()))
    ]


def monster_table_rows(monsters: tuple[Monster, ...]) -> list[tuple[str, str, str, str]]:
    """Return sorted monster rows for table widgets."""
    return [
        (
            monster.monster_id,
            monster.name,
            str(monster.challenge_rating),
            monster.creature_type.value,
        )
        for monster in sorted(
            monsters,
            key=lambda monster: (monster.challenge_rating, monster.name),
        )
    ]
