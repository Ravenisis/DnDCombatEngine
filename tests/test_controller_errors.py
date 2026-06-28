from dnd_combat_engine.controllers import capture_controller_error


def test_capture_controller_error_returns_value_on_success() -> None:
    result = capture_controller_error(lambda: 3)

    assert result.ok is True
    assert result.value == 3


def test_capture_controller_error_maps_validation_errors() -> None:
    result = capture_controller_error(lambda: (_ for _ in ()).throw(ValueError("bad input")))

    assert result.ok is False
    assert result.error.code == "validation_error"
    assert result.error.message == "bad input"


def test_capture_controller_error_maps_key_errors() -> None:
    result = capture_controller_error(lambda: (_ for _ in ()).throw(KeyError("missing")))

    assert result.ok is False
    assert result.error.code == "not_found"

