from dnd_combat_engine.engine import AttackRequest
from dnd_combat_engine.models import (
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    Weapon,
)
from dnd_combat_engine.models.resources import ResourcePool
from dnd_combat_engine.rules import (
    BlessFeature,
    DivineSmiteFeature,
    FeatureEngine,
    GreatWeaponMasterFeature,
    HexFeature,
    HuntersMarkFeature,
    RageFeature,
    SharpshooterFeature,
    SneakAttackFeature,
)
from dnd_combat_engine.services import CombatService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def make_weapon() -> Weapon:
    return Weapon(
        name="Rapier",
        damage=DamageProfile((DamageComponent("1d8", DamageType.PIERCING),)),
    )


def make_character(
    character_id: str,
    name: str,
    level: int = 1,
    features: tuple[str, ...] = (),
    hp: int = 20,
) -> Character:
    return Character(
        character_id=character_id,
        name=name,
        hit_points=HitPoints(current=hp, maximum=hp),
        level=level,
        features=features,
    )


def test_bless_feature_adds_attack_bonus_die() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        attacker=make_character("cleric", "Cleric"),
        target=target,
        weapon=make_weapon(),
        target_armor_class=15,
        active_features=("Bless",),
    )
    service = CombatService(feature_engine=FeatureEngine([BlessFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([13, 2, 4]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.attack_bonus_rolls[0].notation == "1d4"
    assert result.attack_total == 15
    assert result.damage_total == 4


def test_sneak_attack_feature_adds_level_scaled_extra_damage() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        attacker=make_character("rogue", "Rogue", level=5, features=("Sneak Attack",)),
        target=target,
        weapon=make_weapon(),
        target_armor_class=12,
        active_features=("Sneak Attack",),
    )
    service = CombatService(feature_engine=FeatureEngine([SneakAttackFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([12, 4, 1, 2, 3]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.damage_by_type == {DamageType.PIERCING: 10}
    assert result.damage_total == 10
    assert target.hit_points.current == 10


def test_hunters_mark_feature_adds_extra_damage_when_known_and_active() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        attacker=make_character("ranger", "Ranger", features=("Hunter's Mark",)),
        target=target,
        weapon=make_weapon(),
        target_armor_class=12,
        active_features=("Hunter's Mark",),
    )
    service = CombatService(feature_engine=FeatureEngine([HuntersMarkFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([12, 4, 5]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.damage_total == 9


def test_inactive_feature_does_not_change_attack() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        attacker=make_character("rogue", "Rogue", level=5, features=("Sneak Attack",)),
        target=target,
        weapon=make_weapon(),
        target_armor_class=12,
    )
    service = CombatService(feature_engine=FeatureEngine([SneakAttackFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([12, 4]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.damage_total == 4


def test_divine_smite_spends_spell_slot_and_adds_radiant_damage() -> None:
    target = make_character("target", "Target")
    attacker = make_character("paladin", "Paladin", features=("Divine Smite",))
    attacker.resources["spell_slot_2"] = ResourcePool("spell_slot_2", current=1, maximum=1)
    request = AttackRequest(
        attacker=attacker,
        target=target,
        weapon=make_weapon(),
        target_armor_class=12,
        active_features=("Divine Smite",),
    )
    service = CombatService(feature_engine=FeatureEngine([DivineSmiteFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([12, 4, 1, 2, 3]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.damage_by_type[DamageType.PIERCING] == 4
    assert result.damage_by_type[DamageType.RADIANT] == 6
    assert attacker.resources["spell_slot_2"].current == 0


def test_great_weapon_master_feature_applies_power_attack_tradeoff() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        attacker=make_character("fighter", "Fighter", features=("Great Weapon Master",)),
        target=target,
        weapon=make_weapon(),
        target_armor_class=10,
        attack_bonus=5,
        active_features=("Great Weapon Master",),
    )
    service = CombatService(feature_engine=FeatureEngine([GreatWeaponMasterFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([10, 4]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.attack_total == 10
    assert result.damage_total == 14


def test_hex_and_rage_features_add_damage() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        attacker=make_character("barbarian", "Barbarian", level=9, features=("Hex", "Rage")),
        target=target,
        weapon=make_weapon(),
        target_armor_class=12,
        active_features=("Hex", "Rage"),
    )
    service = CombatService(feature_engine=FeatureEngine([HexFeature(), RageFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([12, 4, 6]))  # type: ignore[arg-type]

    assert result.damage_by_type[DamageType.PIERCING] == 4
    assert result.damage_by_type[DamageType.NECROTIC] == 6
    assert result.damage_total == 13


def test_sharpshooter_feature_matches_power_attack_tradeoff() -> None:
    target = make_character("target", "Target")
    request = AttackRequest(
        attacker=make_character("ranger", "Ranger", features=("Sharpshooter",)),
        target=target,
        weapon=make_weapon(),
        target_armor_class=10,
        attack_bonus=5,
        active_features=("Sharpshooter",),
    )
    service = CombatService(feature_engine=FeatureEngine([SharpshooterFeature()]))

    result = service.resolve_attack(request, rng=SequenceRng([10, 4]))  # type: ignore[arg-type]

    assert result.hit is True
    assert result.damage_total == 14
