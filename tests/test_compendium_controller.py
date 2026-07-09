from fractions import Fraction

from dnd_combat_engine.controllers import CompendiumController
from dnd_combat_engine.models import (
    AbilityScores,
    DamageType,
    EffectDefinition,
    EffectKind,
    HitPoints,
    Monster,
    Spell,
    SpellSchool,
    TargetProfile,
)
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import MonsterService, PersistenceService, SpellService


def make_controller(tmp_path) -> CompendiumController:
    return CompendiumController(
        monster_service=MonsterService(),
        spell_service=SpellService(),
        persistence_service=PersistenceService(JsonFileStore(tmp_path)),
    )


def test_compendium_controller_loads_and_filters_spells(tmp_path) -> None:
    controller = make_controller(tmp_path)
    shield = Spell(
        spell_id="shield",
        name="Shield",
        level=1,
        school=SpellSchool.ABJURATION,
        casting_time="1 reaction",
        range_text="Self",
        duration="1 round",
    )
    controller.persistence_service.save_spell(shield)

    level_one_spells = controller.spells_by_level(1)

    assert controller.load_spell("shield") == shield
    assert shield in level_one_spells
    assert all(spell.level == 1 for spell in level_one_spells)


def test_compendium_controller_loads_and_filters_monsters(tmp_path) -> None:
    controller = make_controller(tmp_path)
    monster = Monster(
        monster_id="imp",
        name="Imp",
        armor_class=13,
        hit_points=HitPoints(10, 10),
        abilities=AbilityScores(dexterity=17),
        challenge_rating=Fraction(1),
        damage_resistances=(DamageType.FIRE,),
    )
    controller.persistence_service.save_monster(monster)

    assert controller.load_monster("imp") == monster
    assert controller.monsters_by_challenge(maximum=1) == (monster,)
    assert controller.monsters_resistant_to(DamageType.FIRE) == (monster,)


def test_compendium_controller_loads_action_effects(tmp_path) -> None:
    controller = make_controller(tmp_path)
    action = EffectDefinition(
        effect_id="weapon_attack",
        name="Weapon Attack",
        effect_kind=EffectKind.ATTACK,
        target_profile=TargetProfile.ONE_CREATURE,
        range_text="Weapon range",
        dice="weapon_damage",
    )
    controller.persistence_service.store.save("actions", "weapon_attack", action.to_dict())

    assert controller.load_action_effect("weapon_attack") == action
    assert controller.action_effects() == (action,)
