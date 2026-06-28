from dnd_combat_engine.models import Armor, DamageComponent, DamageProfile, DamageType, Weapon


def test_weapon_round_trips_to_plain_data() -> None:
    weapon = Weapon(
        name="Longbow",
        damage=DamageProfile((DamageComponent("1d8", DamageType.PIERCING),)),
        properties=("ammunition", "two-handed"),
        range_normal=150,
        range_long=600,
    )

    restored = Weapon.from_dict(weapon.to_dict())

    assert restored == weapon


def test_armor_round_trips_to_plain_data() -> None:
    armor = Armor(name="Chain Mail", armor_class=16, stealth_disadvantage=True)

    restored = Armor.from_dict(armor.to_dict())

    assert restored == armor

