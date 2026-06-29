from pathlib import Path

from dnd_combat_engine.models import Campaign, Character, Encounter, Monster, Spell, Weapon
from dnd_combat_engine.persistence import JsonFileStore

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


def test_seed_data_loads_with_domain_models() -> None:
    store = JsonFileStore(DATA_ROOT)

    assert Character.from_dict(store.load("characters", "vale")).name == "Vale"
    assert Campaign.from_dict(store.load("campaigns", "starter_campaign")).character_ids
    assert Monster.from_dict(store.load("monsters", "goblin")).name == "Goblin"
    assert Spell.from_dict(store.load("spells", "bless")).name == "Bless"
    assert Encounter.from_dict(store.load("encounters", "roadside_ambush")).participants
    assert Weapon.from_dict(store.load("equipment", "rapier")).name == "Rapier"
