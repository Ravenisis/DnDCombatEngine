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


def test_cli_quick_attack_outputs_combat_log(capsys) -> None:
    exit_code = main(["--data-root", "data", "quick-attack"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Vale" in output

