from fractions import Fraction

import pytest

from dnd_combat_engine.models import (
    Armor,
    Condition,
    ConditionName,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    RuleSource,
    Spell,
    SpellSchool,
    Weapon,
)
from dnd_combat_engine.models.abilities import AbilityScores
from dnd_combat_engine.models.monsters import Monster


def test_rule_source_round_trips_and_exposes_srd_factory() -> None:
    source = RuleSource.srd_5_2_1("spells.md#cure-wounds")

    restored = RuleSource.from_dict(source.to_dict())

    assert restored == source
    assert restored.version == "5.2.1"
    assert "Creative Commons" in restored.license_name


def test_rule_source_rejects_missing_attribution_fields() -> None:
    with pytest.raises(ValueError):
        RuleSource("", "5.2.1", "CC BY 4.0", "https://example.test", "Attribution")
    with pytest.raises(ValueError):
        RuleSource("SRD", "5.2.1", "CC BY 4.0", "https://example.test", "")


def test_rule_source_survives_rule_bearing_model_round_trips() -> None:
    source = RuleSource.srd_5_2_1("equipment.md#weapons")
    weapon = Weapon(
        name="Mace",
        damage=DamageProfile((DamageComponent("1d6", DamageType.BLUDGEONING),)),
        rule_source=source,
    )
    armor = Armor("Chain Mail", 16, rule_source=source)
    spell = Spell(
        spell_id="cure-wounds",
        name="Cure Wounds",
        level=1,
        school=SpellSchool.EVOCATION,
        casting_time="Action",
        range_text="Touch",
        duration="Instantaneous",
        rule_source=source,
    )
    condition = Condition(ConditionName.POISONED, rule_source=source)
    monster = Monster(
        monster_id="skeleton",
        name="Skeleton",
        armor_class=13,
        hit_points=HitPoints(13, 13),
        abilities=AbilityScores(),
        challenge_rating=Fraction(1, 4),
        rule_source=source,
    )

    assert Weapon.from_dict(weapon.to_dict()).rule_source == source
    assert Armor.from_dict(armor.to_dict()).rule_source == source
    assert Spell.from_dict(spell.to_dict()).rule_source == source
    assert Condition.from_dict(condition.to_dict()).rule_source == source
    assert Monster.from_dict(monster.to_dict()).rule_source == source
