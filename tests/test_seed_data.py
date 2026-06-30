from pathlib import Path

from dnd_combat_engine.models import Campaign, Character, Encounter, Monster, Spell, Weapon
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
