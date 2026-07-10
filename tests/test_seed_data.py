import json
from pathlib import Path

from dnd_combat_engine.models import (
    Campaign,
    Character,
    EffectDefinition,
    Encounter,
    InventoryItem,
    Monster,
    Spell,
    Weapon,
)
from dnd_combat_engine.persistence import JsonFileStore

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


def test_seed_data_loads_with_domain_models() -> None:
    store = JsonFileStore(DATA_ROOT)

    assert Character.from_dict(store.load("characters", "vale")).name == "Vale"
    assert Character.from_dict(store.load("characters", "ravenisis")).name == "Ravenisis"
    assert Character.from_dict(store.load("characters", "bran")).name == "Bran"
    campaign = Campaign.from_dict(store.load("campaigns", "starter_campaign"))
    assert campaign.character_ids == ("ravenisis", "bran")
    assert campaign.encounter_ids == ("roadside_ambush", "crypt_entry")
    assert Monster.from_dict(store.load("monsters", "goblin")).name == "Goblin"
    assert Spell.from_dict(store.load("spells", "bless")).name == "Bless"
    assert Spell.from_dict(store.load("spells", "cure_wounds")).name == "Cure Wounds"
    assert Encounter.from_dict(store.load("encounters", "roadside_ambush")).participants
    assert Encounter.from_dict(store.load("encounters", "crypt_entry")).participants
    assert Weapon.from_dict(store.load("equipment", "rapier")).name == "Rapier"
    assert store.load("srd_catalog", "srd_spells_level_0_5")["entries"]
    srd_items = json.loads((DATA_ROOT / "equipment" / "srd_equipment.json").read_text())
    assert len(srd_items) >= 200
    assert InventoryItem.from_dict(srd_items[0]).name
    assert any(item["name"] == "Potion of Healing" for item in srd_items)
    assert any(item["name"] == "Playing Card Set" for item in srd_items)
    assert any(item["name"] == "Airship" for item in srd_items)


def test_seed_spells_define_data_backed_effects_for_core_actions() -> None:
    store = JsonFileStore(DATA_ROOT)

    expected = {
        "beacon_of_hope": "beacon-of-hope-buff",
        "bless": "bless-buff",
        "cure_wounds": "cure-wounds-healing",
        "guiding_bolt": "guiding-bolt-damage",
        "lesser_restoration": "lesser-restoration-condition",
        "light": "light-utility",
        "revivify": "revivify-healing",
        "thaumaturgy": "thaumaturgy-utility",
    }

    for spell_id, effect_id in expected.items():
        spell = Spell.from_dict(store.load("spells", spell_id))
        assert effect_id in {effect.effect_id for effect in spell.effects}
        assert all(effect.range_text for effect in spell.effects)


def test_seed_action_effects_define_weapon_and_unarmed_attacks() -> None:
    store = JsonFileStore(DATA_ROOT)

    weapon_attack = EffectDefinition.from_dict(store.load("actions", "weapon_attack"))
    unarmed_attack = EffectDefinition.from_dict(store.load("actions", "unarmed_attack"))

    assert weapon_attack.effect_id == "weapon_attack"
    assert weapon_attack.dice == "weapon_damage"
    assert unarmed_attack.effect_id == "unarmed_attack"
    assert unarmed_attack.range_text == "5 feet"
