from dnd_combat_engine.app import create_app
from dnd_combat_engine.gui.commands import GuiCommandDispatcher


def test_gui_command_dispatcher_rolls_d20() -> None:
    dispatcher = GuiCommandDispatcher(create_app("data"))

    result = dispatcher.dispatch("dice.roll_d20")

    assert result.ok
    assert result.value is not None
    assert result.value.startswith("1d20: ")


def test_gui_command_dispatcher_runs_quick_attack() -> None:
    dispatcher = GuiCommandDispatcher(create_app("data"))

    result = dispatcher.dispatch("combat.quick_attack")

    assert result.ok
    assert result.value is not None
    assert "Vale" in result.value
    assert "Goblin" in result.value


def test_gui_command_dispatcher_loads_starter_campaign() -> None:
    dispatcher = GuiCommandDispatcher(create_app("data"))

    result = dispatcher.dispatch("campaign.load_starter")

    assert result.ok
    assert result.value is not None
    assert "Starter Campaign" in result.value
    assert "2 characters" in result.value


def test_gui_command_dispatcher_activates_starter_campaign(tmp_path) -> None:
    from dnd_combat_engine.models import Campaign
    from dnd_combat_engine.persistence import JsonFileStore

    store = JsonFileStore(tmp_path)
    campaign = Campaign("starter_campaign", "Starter Campaign")
    store.save("campaigns", campaign.campaign_id, campaign.to_dict())
    dispatcher = GuiCommandDispatcher(create_app(tmp_path))

    result = dispatcher.dispatch("campaign.activate_starter")

    assert result.ok
    assert result.value == "Starter Campaign: active"
    assert Campaign.from_dict(store.load("campaigns", "starter_campaign")).status == "active"


def test_gui_command_dispatcher_reports_unknown_commands() -> None:
    dispatcher = GuiCommandDispatcher(create_app("data"))

    result = dispatcher.dispatch("missing.command")

    assert not result.ok
    assert result.error is not None
    assert result.error.code == "unknown_command"
