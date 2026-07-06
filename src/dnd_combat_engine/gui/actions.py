"""GUI action specifications."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuiActionSpec:
    """Declarative GUI action metadata."""

    action_id: str
    menu: str
    text: str
    status_tip: str
    shortcut: str | None = None
    submenu: str | None = None

    def __post_init__(self) -> None:
        """Validate action metadata."""
        if not self.action_id:
            raise ValueError("action_id is required")
        if not self.menu:
            raise ValueError("menu is required")
        if not self.text:
            raise ValueError("text is required")
        if not self.status_tip:
            raise ValueError("status_tip is required")


def default_action_specs() -> tuple[GuiActionSpec, ...]:
    """Return default GUI action specifications."""
    return (
        GuiActionSpec("file.exit", "File", "Exit", "Close the application", "Ctrl+Q"),
        GuiActionSpec("view.reset_layout", "View", "Reset Layout", "Restore dock layout"),
        GuiActionSpec(
            "character.spellbook",
            "Character",
            "Spellbook",
            "Open the party leader spellbook",
        ),
        GuiActionSpec(
            "character.abilities",
            "Character",
            "Abilities",
            "Open the party leader abilities",
        ),
        GuiActionSpec(
            "character.inventory",
            "Character",
            "Inventory",
            "Open the party leader inventory",
        ),
        GuiActionSpec(
            "character.break_concentration",
            "Character",
            "Break Concentration",
            "End the active concentration spell",
        ),
        GuiActionSpec(
            "campaign.load_starter",
            "Campaign",
            "Load Starter Campaign",
            "Load the starter campaign",
        ),
        GuiActionSpec(
            "campaign.activate_starter",
            "Campaign",
            "Activate Starter Campaign",
            "Activate and save the starter campaign",
        ),
        GuiActionSpec(
            "campaign.new",
            "Campaign",
            "Begin New Campaign",
            "Create and open a new campaign",
        ),
        GuiActionSpec(
            "campaign.close",
            "Campaign",
            "Close Current Campaign",
            "Close the active campaign workspace",
        ),
        GuiActionSpec(
            "campaign.add_party_member",
            "Campaign",
            "Add Party Member",
            "Add an existing character to the active campaign",
        ),
        GuiActionSpec(
            "campaign.set_party_leader",
            "Campaign",
            "Set Party Leader",
            "Set which party member owns the active spellbook",
        ),
        GuiActionSpec(
            "campaign.long_rest",
            "Campaign",
            "Long Rest",
            "Fully heal party members and restore spell slots",
            submenu="Rest",
        ),
        GuiActionSpec(
            "campaign.short_rest",
            "Campaign",
            "Short Rest",
            "Recover short-rest resources and partial hit points",
            submenu="Rest",
        ),
        GuiActionSpec(
            "campaign.import_pdf",
            "Campaign",
            "PDF",
            "Import a character sheet from a PDF file",
            submenu="Upload Character Sheet",
        ),
        GuiActionSpec(
            "campaign.import_url",
            "Campaign",
            "URL",
            "Import a character sheet from a public URL",
            submenu="Upload Character Sheet",
        ),
        GuiActionSpec("combat.quick_attack", "Combat", "Quick Attack", "Run a sample attack"),
        GuiActionSpec("dice.roll_d20", "Dice", "Roll d20", "Roll a d20", "Ctrl+R"),
    )


def action_specs_by_menu(specs: tuple[GuiActionSpec, ...]) -> dict[str, tuple[GuiActionSpec, ...]]:
    """Group action specifications by menu name."""
    grouped: dict[str, list[GuiActionSpec]] = {}
    for spec in specs:
        grouped.setdefault(spec.menu, []).append(spec)
    return {menu: tuple(items) for menu, items in grouped.items()}
