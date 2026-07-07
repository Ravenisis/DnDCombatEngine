import pytest

from dnd_combat_engine.models import (
    DamageComponent,
    DamageProfile,
    DamageType,
    EffectDefinition,
    EffectKind,
    Spell,
    SpellSchool,
    TargetProfile,
)
from dnd_combat_engine.services import SpellService


def make_spell(
    spell_id: str,
    name: str,
    level: int,
    concentration: bool = False,
    damaging: bool = False,
) -> Spell:
    return Spell(
        spell_id=spell_id,
        name=name,
        level=level,
        school=SpellSchool.EVOCATION,
        casting_time="1 action",
        range_text="60 feet",
        duration="Instantaneous",
        concentration=concentration,
        damage=DamageProfile((DamageComponent("1d6", DamageType.FIRE),)) if damaging else None,
    )


def test_spell_service_filters_by_level_and_sorts_by_name() -> None:
    spells = [
        make_spell("magic-missile", "Magic Missile", 1),
        make_spell("burning-hands", "Burning Hands", 1),
        make_spell("fire-bolt", "Fire Bolt", 0),
    ]

    assert [spell.spell_id for spell in SpellService().by_level(spells, 1)] == [
        "burning-hands",
        "magic-missile",
    ]


def test_spell_service_filters_concentration_and_damage_spells() -> None:
    spells = [
        make_spell("bless", "Bless", 1, concentration=True),
        make_spell("fire-bolt", "Fire Bolt", 0, damaging=True),
        make_spell("mending", "Mending", 0),
    ]
    service = SpellService()

    assert [spell.spell_id for spell in service.concentration_spells(spells)] == ["bless"]
    assert [spell.spell_id for spell in service.damaging_spells(spells)] == ["fire-bolt"]


def test_spell_service_treats_damage_effects_as_damaging_spells() -> None:
    spell = make_spell("guiding-bolt", "Guiding Bolt", 1)
    spell = Spell.from_dict(
        {
            **spell.to_dict(),
            "effects": [
                EffectDefinition(
                    effect_id="guiding-bolt-damage",
                    name="Guiding Bolt",
                    effect_kind=EffectKind.DAMAGE,
                    target_profile=TargetProfile.ONE_CREATURE,
                    dice="4d6",
                ).to_dict()
            ],
        }
    )

    assert SpellService().damaging_spells([spell]) == (spell,)


def test_spell_service_rejects_invalid_level() -> None:
    with pytest.raises(ValueError):
        SpellService().by_level([], 10)
