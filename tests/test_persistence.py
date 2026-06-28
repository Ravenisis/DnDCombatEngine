from dnd_combat_engine.models import Character, HitPoints
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import PersistenceService


def test_persistence_service_saves_and_loads_character(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    character = Character(
        character_id="fighter-1",
        name="Bran",
        hit_points=HitPoints(current=12, maximum=12),
    )

    service.save_character(character)

    assert service.list_character_ids() == ["fighter-1"]
    assert service.load_character("fighter-1") == character


def test_store_lists_missing_collection_as_empty(tmp_path) -> None:
    store = JsonFileStore(tmp_path)

    assert store.list_ids("characters") == []


def test_store_rejects_missing_collection_or_id(tmp_path) -> None:
    store = JsonFileStore(tmp_path)

    for collection, entity_id in [("", "x"), ("characters", "")]:
        try:
            store.save(collection, entity_id, {})
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def test_store_rejects_non_object_json(tmp_path) -> None:
    path = tmp_path / "characters"
    path.mkdir()
    (path / "bad.json").write_text("[]", encoding="utf-8")
    store = JsonFileStore(tmp_path)

    try:
        store.load("characters", "bad")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
