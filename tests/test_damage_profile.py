import pytest

from dnd_combat_engine.models import DamageComponent, DamageProfile, DamageType


def test_damage_profile_supports_multiple_damage_types() -> None:
    profile = DamageProfile((DamageComponent("1d8", DamageType.PIERCING),))

    flaming = profile.add(DamageComponent("1d6", DamageType.FIRE))

    assert [component.damage_type for component in flaming.components] == [
        DamageType.PIERCING,
        DamageType.FIRE,
    ]


def test_damage_profile_requires_components() -> None:
    with pytest.raises(ValueError):
        DamageProfile(())

