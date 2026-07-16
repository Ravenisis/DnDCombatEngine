import json
from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp, create_app


def test_create_app_wires_controllers_to_seed_data() -> None:
    app = create_app(Path(__file__).resolve().parents[1] / "data")

    assert isinstance(app, DnDCombatEngineApp)
    assert app.character_imports is not None
    assert app.campaigns.load("starter_campaign").name == "Starter Campaign"
    assert app.characters.load("bran").name == "Bran"
    assert app.characters.load("vale").name == "Vale"
    assert app.compendium.load_monster("goblin").name == "Goblin"
    assert app.dice.describe("1d20")["average"] == 10.5


def test_seed_data_exposes_configured_level_six_cleric_spellbook() -> None:
    app = create_app(Path(__file__).resolve().parents[1] / "data")

    spell_ids = app.compendium.class_spell_ids("cleric", 3)
    names = {app.compendium.load_spell(spell_id).name for spell_id in spell_ids}

    assert {"Guidance", "Detect Magic", "Spiritual Weapon", "Water Walk"} <= names
    assert {"Wardaway", "Deryan's Helpful Homunculi", "Laeral's Silver Lance"} <= names
    assert all(app.compendium.load_spell(spell_id).level <= 3 for spell_id in spell_ids)


def test_create_app_upgrades_legacy_inventory_metadata(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "data" / "characters" / "ravenisis.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    canonical_inventory = {
        item["item_id"]: item for item in payload["inventory"] if item["item_id"] != "warhammer"
    }
    payload["inventory"] = []
    for canonical in canonical_inventory.values():
        legacy = {
            **canonical,
            "category": "other",
            "weight": 0,
            "purchase_price_cp": 0,
            "notes": None,
            "tags": [],
            "subcategory": "",
        }
        payload["inventory"].append(legacy)
    characters = tmp_path / "characters"
    characters.mkdir()
    (characters / "ravenisis.json").write_text(json.dumps(payload), encoding="utf-8")

    app = create_app(tmp_path)
    ravenisis = app.characters.load("ravenisis")
    by_id = {item.item_id: item for item in ravenisis.inventory}

    for item_id, canonical in canonical_inventory.items():
        assert by_id[item_id].category.value == canonical["category"]
        assert by_id[item_id].weight == canonical["weight"]
        assert by_id[item_id].purchase_price_cp == canonical["purchase_price_cp"]
        assert by_id[item_id].notes == canonical["notes"]
        assert by_id[item_id].tags == tuple(canonical["tags"])
        assert by_id[item_id].subcategory == canonical.get("subcategory", "")
    assert by_id["warhammer"].category.value == "weapon"
    assert by_id["warhammer"].notes is not None


def test_create_app_restores_legacy_channel_divinity_metadata(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "data" / "characters" / "ravenisis.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["features"] = []
    payload["resources"].pop("channel_divinity", None)
    characters = tmp_path / "characters"
    characters.mkdir()
    (characters / "ravenisis.json").write_text(json.dumps(payload), encoding="utf-8")

    app = create_app(tmp_path)
    ravenisis = app.characters.load("ravenisis")

    assert "Channel Divinity: Turn Undead" in ravenisis.features
    assert "Channel Divinity: Preserve Life" in ravenisis.features
    assert ravenisis.resources["channel_divinity"].current == 2
    assert ravenisis.resources["channel_divinity"].maximum == 2


def test_create_app_merges_missing_channel_options_without_replacing_features(
    tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().parents[1] / "data" / "characters" / "ravenisis.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["features"] = ["Custom Feature", "Channel Divinity: Turn Undead"]
    payload["resources"].pop("channel_divinity", None)
    characters = tmp_path / "characters"
    characters.mkdir()
    (characters / "ravenisis.json").write_text(json.dumps(payload), encoding="utf-8")

    app = create_app(tmp_path)
    ravenisis = app.characters.load("ravenisis")

    assert "Custom Feature" in ravenisis.features
    assert "Channel Divinity: Turn Undead" in ravenisis.features
    assert "Channel Divinity: Preserve Life" in ravenisis.features
    assert ravenisis.resources["channel_divinity"].maximum == 2
