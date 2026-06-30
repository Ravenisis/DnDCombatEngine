"""Dialog helpers for importing character sheets."""

from __future__ import annotations


def choose_character_pdf(qt, parent) -> str | None:
    """Prompt for a character sheet PDF and return the selected path."""
    dialog = getattr(qt.QtWidgets, "QFileDialog", None)
    if dialog is None:
        return None
    selected = dialog.getOpenFileName(
        parent,
        "Import Character PDF",
        "",
        "PDF files (*.pdf);;All files (*.*)",
    )
    path = selected[0] if isinstance(selected, tuple) else selected
    return str(path) if path else None


def ask_character_url(qt, parent) -> str | None:
    """Prompt for a public character sheet URL."""
    dialog = getattr(qt.QtWidgets, "QInputDialog", None)
    if dialog is None:
        return None
    selected = dialog.getText(
        parent,
        "Import Character URL",
        "Character sheet URL:",
    )
    if isinstance(selected, tuple):
        text, accepted = selected
        return str(text).strip() if accepted and str(text).strip() else None
    return str(selected).strip() if selected else None


def ask_campaign_name(qt, parent) -> str | None:
    """Prompt for a new campaign name."""
    dialog = getattr(qt.QtWidgets, "QInputDialog", None)
    if dialog is None:
        return None
    selected = dialog.getText(
        parent,
        "Begin New Campaign",
        "Campaign name:",
    )
    if isinstance(selected, tuple):
        text, accepted = selected
        return str(text).strip() if accepted and str(text).strip() else None
    return str(selected).strip() if selected else None
