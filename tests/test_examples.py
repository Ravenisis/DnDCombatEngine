from examples.quick_attack import main


def test_quick_attack_example_runs(capsys) -> None:
    main()

    output = capsys.readouterr().out

    assert "Vale" in output
    assert "Goblin HP:" in output

