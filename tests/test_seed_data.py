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
    assert len(srd_items) >= 625
    srd_items_by_name = {item["name"]: item for item in srd_items}
    assert srd_items_by_name["Spell Scroll (Level 9)"]["category"] == "consumable"
    assert "magic item" in srd_items_by_name["Potion of Flying"]["tags"]
    assert "requires attunement" in srd_items_by_name["Ring of Protection"]["tags"]
    assert "trade good" in srd_items_by_name["Saffron (1 lb.)"]["tags"]
    assert "bonus:+3" in srd_items_by_name["Vorpal Sword"]["tags"]
    assert "gemstone" in srd_items_by_name["Diamond Gemstone"]["tags"]
    assert "art object" in srd_items_by_name["Jeweled Platinum Ring"]["tags"]
    assert "manual" in srd_items_by_name["Manual of Gainful Exercise"]["tags"]
    assert "cursed" in srd_items_by_name["Berserker Axe"]["tags"]
    assert "healing" in srd_items_by_name["Potion of Healing (Supreme)"]["tags"]
    assert "figurine" in srd_items_by_name[
        "Figurine of Wondrous Power (Silver Raven)"
    ]["tags"]
    assert "force" in srd_items_by_name["Cube of Force"]["tags"]
    assert "talisman" in srd_items_by_name["Talisman of Pure Good"]["tags"]
    assert "shield" in srd_items_by_name["Animated Shield"]["tags"]
    assert "damage:radiant" in srd_items_by_name["Holy Avenger"]["tags"]


def test_seed_spells_define_data_backed_effects_for_core_actions() -> None:
    store = JsonFileStore(DATA_ROOT)

    expected = {
        "beacon_of_hope": "beacon-of-hope-buff",
        "bless": "bless-buff",
        "cure_wounds": "cure-wounds-healing",
        "guiding_bolt": "guiding-bolt-damage",
        "hex": "hex-curse",
        "lesser_restoration": "lesser-restoration-condition",
        "light": "light-utility",
        "revivify": "revivify-healing",
        "sacred_flame": "sacred-flame-damage",
        "spiritual_weapon": "spiritual-weapon-attack",
        "thaumaturgy": "thaumaturgy-utility",
    }

    for spell_id, effect_id in expected.items():
        spell = Spell.from_dict(store.load("spells", spell_id))
        assert effect_id in {effect.effect_id for effect in spell.effects}
        assert all(effect.range_text for effect in spell.effects)
        assert all(effect.interactions for effect in spell.effects)

    guiding_bolt = Spell.from_dict(store.load("spells", "guiding_bolt"))
    damage = next(
        effect for effect in guiding_bolt.effects if effect.effect_id == "guiding-bolt-damage"
    )
    assert {
        interaction.outcome_kind.value for interaction in damage.interactions
    } >= {"apply_damage", "grant_advantage"}
    assert damage.interactions[0].scaling["per_slot_level_above_base"] == "+1d6 damage"


def test_seed_action_effects_define_weapon_and_unarmed_attacks() -> None:
    store = JsonFileStore(DATA_ROOT)

    weapon_attack = EffectDefinition.from_dict(store.load("actions", "weapon_attack"))
    unarmed_attack = EffectDefinition.from_dict(store.load("actions", "unarmed_attack"))

    assert weapon_attack.effect_id == "weapon_attack"
    assert weapon_attack.dice == "weapon_damage"
    assert {interaction.outcome_kind.value for interaction in weapon_attack.interactions} >= {
        "apply_damage",
        "narrate",
    }
    assert unarmed_attack.effect_id == "unarmed_attack"
    assert unarmed_attack.range_text == "5 feet"
    assert unarmed_attack.interactions
