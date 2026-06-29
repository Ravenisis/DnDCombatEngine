from fractions import Fraction

from dnd_combat_engine.gui.tables import (
    campaign_table_rows,
    monster_table_rows,
    spell_table_rows,
)
from dnd_combat_engine.models import (
    AbilityScores,
    Campaign,
    CreatureType,
    HitPoints,
    Monster,
    Spell,
    SpellSchool,
)


def test_campaign_table_rows_sort_by_name() -> None:
    starter = Campaign("starter", "Starter", encounter_ids=("roadside_ambush",))
    crypts = Campaign("crypts", "Crypts", encounter_ids=("crypt_entry", "vault"))

    assert campaign_table_rows((starter, crypts)) == [
        ("crypts", "Crypts", "planned", "2"),
        ("starter", "Starter", "planned", "1"),
    ]


def test_spell_table_rows_sort_by_level_then_name() -> None:
    fireball = Spell(
        spell_id="fireball",
        name="Fireball",
        level=3,
        school=SpellSchool.EVOCATION,
        casting_time="1 action",
        range_text="150 feet",
        duration="Instantaneous",
    )
    bless = Spell(
        spell_id="bless",
        name="Bless",
        level=1,
        school=SpellSchool.ENCHANTMENT,
        casting_time="1 action",
        range_text="30 feet",
        duration="Concentration, up to 1 minute",
    )

    assert spell_table_rows((fireball, bless)) == [
        ("bless", "Bless", "1", "enchantment"),
        ("fireball", "Fireball", "3", "evocation"),
    ]


def test_monster_table_rows_sort_by_challenge_then_name() -> None:
    ogre = _monster("ogre", "Ogre", Fraction(2), CreatureType.GIANT)
    goblin = _monster("goblin", "Goblin", Fraction(1, 4), CreatureType.HUMANOID)

    assert monster_table_rows((ogre, goblin)) == [
        ("goblin", "Goblin", "1/4", "humanoid"),
        ("ogre", "Ogre", "2", "giant"),
    ]


def _monster(
    monster_id: str,
    name: str,
    challenge_rating: Fraction,
    creature_type: CreatureType,
) -> Monster:
    return Monster(
        monster_id=monster_id,
        name=name,
        armor_class=12,
        hit_points=HitPoints(current=7, maximum=7),
        abilities=AbilityScores(),
        challenge_rating=challenge_rating,
        creature_type=creature_type,
    )
