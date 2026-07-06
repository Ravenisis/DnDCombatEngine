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
        "character.spellbook",
        "campaign.load_starter",
        "campaign.activate_starter",
        "campaign.new",
        "campaign.close",
        "campaign.add_party_member",
        "campaign.set_party_leader",
        "campaign.long_rest",
        "campaign.short_rest",
        "campaign.import_pdf",
        "campaign.import_url",
        "combat.quick_attack",
        "dice.roll_d20",
    }
    assert next(spec for spec in specs if spec.action_id == "dice.roll_d20").shortcut == "Ctrl+R"
    assert next(spec for spec in specs if spec.action_id == "campaign.import_pdf").submenu == (
        "Upload Character Sheet"
    )
    assert next(spec for spec in specs if spec.action_id == "campaign.long_rest").submenu == "Rest"


def test_action_specs_group_by_menu_preserves_order() -> None:
    grouped = action_specs_by_menu(default_action_specs())

    assert tuple(grouped) == ("File", "View", "Character", "Campaign", "Combat", "Dice")
    assert grouped["Character"][0].action_id == "character.spellbook"
    assert grouped["Campaign"][0].action_id == "campaign.load_starter"
    assert grouped["Campaign"][4].action_id == "campaign.add_party_member"
    assert grouped["Campaign"][6].action_id == "campaign.long_rest"
    assert grouped["Campaign"][8].action_id == "campaign.import_pdf"
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
