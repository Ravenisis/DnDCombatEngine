"""Application version metadata displayed to users and attached to reports."""

APP_VERSION = "1.0.3"
VERSION_LAST_MODIFIED_EASTERN = "07/15/2026 03:49 pm"


def about_text() -> str:
    """Return the user-facing application version summary."""
    return (
        f"DnDCombatEngine {APP_VERSION}\n"
        f"Version last modified (Eastern): {VERSION_LAST_MODIFIED_EASTERN}\n"
        "Layered Dungeons & Dragons combat workspace."
    )
