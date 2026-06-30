from dnd_combat_engine.cli import main


def test_cli_roll_command_outputs_result(capsys) -> None:
    exit_code = main(["--data-root", "data", "roll", "1d6+2", "--seed", "1"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "1d6+2:" in output


def test_cli_lists_seed_spell_ids(capsys) -> None:
    exit_code = main(["--data-root", "data", "list-spells"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "bless" in output


def test_cli_lists_seed_campaign_ids(capsys) -> None:
    exit_code = main(["--data-root", "data", "list-campaigns"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "starter_campaign" in output


def test_cli_initializes_user_data(tmp_path, capsys) -> None:
    exit_code = main(["--data-root", str(tmp_path / "user-data"), "init-user-data"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "user-data" in output
    assert (tmp_path / "user-data" / "characters" / "vale.json").exists()


def test_cli_gui_command_handles_missing_pyside6(monkeypatch, capsys) -> None:
    import dnd_combat_engine.gui
    from dnd_combat_engine.gui import GuiDependencyError

    def fake_run_gui(data_root):
        raise GuiDependencyError("Install GUI dependencies")

    monkeypatch.setattr(dnd_combat_engine.gui, "run_gui", fake_run_gui)

    assert main(["--data-root", "data", "gui"]) == 1
    assert "Install GUI dependencies" in capsys.readouterr().err


def test_cli_shows_campaign_details(capsys) -> None:
    exit_code = main(["--data-root", "data", "campaign", "show", "starter_campaign"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Starter Campaign [active]" in output
    assert "ravenisis" in output
    assert "crypt_entry" in output


def test_cli_activates_campaign(tmp_path, capsys) -> None:
    from dnd_combat_engine.models import Campaign
    from dnd_combat_engine.persistence import JsonFileStore

    store = JsonFileStore(tmp_path)
    campaign = Campaign("starter_campaign", "Starter Campaign")
    store.save("campaigns", campaign.campaign_id, campaign.to_dict())

    exit_code = main(["--data-root", str(tmp_path), "campaign", "activate", "starter_campaign"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Starter Campaign [active]" in output
    assert Campaign.from_dict(store.load("campaigns", "starter_campaign")).status == "active"


def test_cli_quick_attack_outputs_combat_log(capsys) -> None:
    exit_code = main(["--data-root", "data", "quick-attack"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Vale" in output


def test_cli_gui_command_delegates_to_gui_runner(monkeypatch) -> None:
    import dnd_combat_engine.gui

    called = {}

    def fake_run_gui(data_root):
        called["data_root"] = data_root
        return 7

    monkeypatch.setattr(dnd_combat_engine.gui, "run_gui", fake_run_gui)

    assert main(["--data-root", "data", "gui"]) == 7
    assert str(called["data_root"]) == "data"
