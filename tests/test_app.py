from pathlib import Path

from dnd_combat_engine.app import DnDCombatEngineApp, create_app


def test_create_app_wires_controllers_to_seed_data() -> None:
    app = create_app(Path(__file__).resolve().parents[1] / "data")

    assert isinstance(app, DnDCombatEngineApp)
    assert app.campaigns.load("starter_campaign").name == "Starter Campaign"
    assert app.characters.load("bran").name == "Bran"
    assert app.characters.load("vale").name == "Vale"
    assert app.compendium.load_monster("goblin").name == "Goblin"
    assert app.dice.describe("1d20")["average"] == 10.5
