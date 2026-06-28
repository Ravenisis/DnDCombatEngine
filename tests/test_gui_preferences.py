import pytest

from dnd_combat_engine.gui.preferences import GuiPreferences


def test_gui_preferences_use_professional_defaults() -> None:
    preferences = GuiPreferences()

    assert preferences.dark_mode is True
    assert preferences.auto_save is True
    assert preferences.confirm_exit is True
    assert preferences.default_dice == "1d20"


def test_gui_preferences_round_trip_to_plain_data() -> None:
    preferences = GuiPreferences(
        dark_mode=False,
        auto_save=False,
        confirm_exit=False,
        default_dice="2d6+3",
    )

    restored = GuiPreferences.from_dict(preferences.to_dict())

    assert restored == preferences


def test_gui_preferences_reject_missing_default_dice() -> None:
    with pytest.raises(ValueError):
        GuiPreferences(default_dice="")
