import pytest

from dnd_combat_engine.gui.actions import (
    GuiActionSpec,
    action_specs_by_menu,
    default_action_specs,
)


def test_default_action_specs_include_core_commands() -> None:
    specs = default_action_specs()

    assert {spec.action_id for spec in specs} >= {
        "file.exit",
        "view.reset_layout",
        "campaign.load_starter",
        "campaign.activate_starter",
        "campaign.new",
        "campaign.close",
        "campaign.import_pdf",
        "campaign.import_url",
        "combat.quick_attack",
        "dice.roll_d20",
    }
    assert next(spec for spec in specs if spec.action_id == "dice.roll_d20").shortcut == "Ctrl+R"
    assert next(spec for spec in specs if spec.action_id == "campaign.import_pdf").submenu == (
        "Upload Character Sheet"
    )


def test_action_specs_group_by_menu_preserves_order() -> None:
    grouped = action_specs_by_menu(default_action_specs())

    assert tuple(grouped) == ("File", "View", "Campaign", "Combat", "Dice")
    assert grouped["Campaign"][0].action_id == "campaign.load_starter"
    assert grouped["Campaign"][4].action_id == "campaign.import_pdf"
    assert grouped["Combat"][0].action_id == "combat.quick_attack"


def test_action_spec_rejects_missing_metadata() -> None:
    with pytest.raises(ValueError):
        GuiActionSpec("", "File", "Exit", "Close")
    with pytest.raises(ValueError):
        GuiActionSpec("file.exit", "", "Exit", "Close")
    with pytest.raises(ValueError):
        GuiActionSpec("file.exit", "File", "", "Close")
    with pytest.raises(ValueError):
        GuiActionSpec("file.exit", "File", "Exit", "")
