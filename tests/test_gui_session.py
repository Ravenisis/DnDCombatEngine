import pytest

from dnd_combat_engine.gui import GuiSession, load_session, save_session


def test_gui_session_round_trips_to_file(tmp_path) -> None:
    path = tmp_path / "session.json"
    session = GuiSession(data_root="data", last_character_id="vale")

    save_session(session, path)

    assert load_session(path) == session


def test_load_session_returns_default_when_missing(tmp_path) -> None:
    assert load_session(tmp_path / "missing.json") == GuiSession()


def test_gui_session_validates_values() -> None:
    with pytest.raises(ValueError):
        GuiSession(data_root="")
    with pytest.raises(ValueError):
        GuiSession(last_character_id="")
    with pytest.raises(ValueError):
        GuiSession(window_width=1)
    with pytest.raises(ValueError):
        GuiSession(window_height=1)


def test_load_session_rejects_non_object_json(tmp_path) -> None:
    path = tmp_path / "session.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        load_session(path)

