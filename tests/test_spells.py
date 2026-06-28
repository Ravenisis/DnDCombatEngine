import pytest

from dnd_combat_engine.models import (
    DamageComponent,
    DamageProfile,
    DamageType,
    Spell,
    SpellSchool,
)


def make_spell() -> Spell:
    return Spell(
        spell_id="fire-bolt",
        name="Fire Bolt",
        level=0,
        school=SpellSchool.EVOCATION,
        casting_time="1 action",
        range_text="120 feet",
        duration="Instantaneous",
        components=("V", "S"),
        damage=DamageProfile((DamageComponent("1d10", DamageType.FIRE),)),
        description="Hurl a mote of fire.",
    )


def test_spell_round_trips_to_plain_data() -> None:
    spell = make_spell()

    restored = Spell.from_dict(spell.to_dict())

    assert restored == spell
    assert restored.is_cantrip is True


def test_spell_without_damage_round_trips() -> None:
    spell = Spell(
        spell_id="bless",
        name="Bless",
        level=1,
        school=SpellSchool.ENCHANTMENT,
        casting_time="1 action",
        range_text="30 feet",
        duration="Concentration, up to 1 minute",
        concentration=True,
    )

    restored = Spell.from_dict(spell.to_dict())

    assert restored == spell
    assert restored.damage is None


def test_spell_rejects_invalid_values() -> None:
    kwargs = {
        "spell_id": "x",
        "name": "X",
        "level": 1,
        "school": SpellSchool.EVOCATION,
        "casting_time": "1 action",
        "range_text": "Self",
        "duration": "Instantaneous",
    }

    with pytest.raises(ValueError):
        Spell(**{**kwargs, "spell_id": ""})
    with pytest.raises(ValueError):
        Spell(**{**kwargs, "name": ""})
    with pytest.raises(ValueError):
        Spell(**{**kwargs, "level": 10})
    with pytest.raises(ValueError):
        Spell(**{**kwargs, "casting_time": ""})
    with pytest.raises(ValueError):
        Spell(**{**kwargs, "range_text": ""})
    with pytest.raises(ValueError):
        Spell(**{**kwargs, "duration": ""})

