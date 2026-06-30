from pathlib import Path

from dnd_combat_engine.models import Campaign, Character
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.utils.paths import bundled_data_root, default_data_root, initialize_user_data


def test_bundled_data_root_contains_seed_data() -> None:
    store = JsonFileStore(bundled_data_root())

    assert Character.from_dict(store.load("characters", "vale")).name == "Vale"
    assert Character.from_dict(store.load("characters", "ravenisis")).name == "Ravenisis"
    assert Campaign.from_dict(store.load("campaigns", "starter_campaign")).character_ids


def test_initialize_user_data_copies_seed_collections(tmp_path) -> None:
    target = initialize_user_data(tmp_path / "app-data")
    store = JsonFileStore(target)

    assert target == tmp_path / "app-data"
    assert store.list_ids("characters") == ["bran", "ravenisis", "vale"]
    assert store.load("campaigns", "starter_campaign")["name"] == "Starter Campaign"


def test_default_data_root_uses_env_override(monkeypatch, tmp_path) -> None:
    target = tmp_path / "env-data"
    monkeypatch.setenv("DND_COMBAT_ENGINE_DATA", str(target))

    assert default_data_root() == target
    assert (target / "characters" / "vale.json").exists()


def test_default_data_root_prefers_source_tree_when_present(monkeypatch) -> None:
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("DND_COMBAT_ENGINE_DATA", raising=False)
    monkeypatch.chdir(project_root)

    assert default_data_root() == project_root / "data"
