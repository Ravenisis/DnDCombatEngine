"""Dialog helpers for importing character sheets."""

from __future__ import annotations

import re

from dnd_combat_engine.models import (
    AbilityScores,
    Armor,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    InventoryItem,
    ItemCategory,
    Weapon,
)
from dnd_combat_engine.models.imports import CharacterImportDraft


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


def ask_character_id(
    qt,
    parent,
    title: str,
    prompt: str,
    character_ids: tuple[str, ...] = (),
) -> str | None:
    """Prompt for a character id, optionally choosing from known ids."""
    dialog = getattr(qt.QtWidgets, "QInputDialog", None)
    if dialog is None:
        return None
    if character_ids and hasattr(dialog, "getItem"):
        selected = dialog.getItem(parent, title, prompt, list(character_ids), 0, False)
    else:
        selected = dialog.getText(parent, title, prompt)
    if isinstance(selected, tuple):
        text, accepted = selected
        return str(text).strip() if accepted and str(text).strip() else None
    return str(selected).strip() if selected else None


def review_character_import(qt, parent, draft: CharacterImportDraft) -> CharacterImportDraft | None:
    """Show an editable review table and return the confirmed draft."""
    dialog_class = getattr(qt.QtWidgets, "QDialog", None)
    table_class = getattr(qt.QtWidgets, "QTableWidget", None)
    item_class = getattr(qt.QtWidgets, "QTableWidgetItem", None)
    if dialog_class is None or table_class is None or item_class is None:
        return draft

    dialog = dialog_class(parent)
    if hasattr(dialog, "setWindowTitle"):
        dialog.setWindowTitle("Confirm Character Import")
    if hasattr(dialog, "resize"):
        dialog.resize(640, 520)

    layout = qt.QtWidgets.QVBoxLayout(dialog)
    table = table_class(0, 2)
    table.setHorizontalHeaderLabels(["Name", "Value"])
    _populate_review_table(qt, table, character_import_review_rows(draft))
    layout.addWidget(table)

    buttons = _review_buttons(qt, dialog)
    if buttons is not None:
        layout.addWidget(buttons)

    while _dialog_accepted(qt, dialog):
        try:
            return draft_from_review_rows(_read_review_table(table))
        except ValueError as exc:
            _show_review_error(qt, dialog, str(exc))
    return None


def character_import_review_rows(draft: CharacterImportDraft) -> list[tuple[str, str]]:
    """Return editable field/value rows for an imported character draft."""
    return [
        ("Name", draft.name),
        ("Level", str(draft.level)),
        ("Current HP", str(draft.hit_points.current)),
        ("Maximum HP", str(draft.hit_points.maximum)),
        ("Temporary HP", str(draft.hit_points.temporary)),
        ("Armor Class", "" if draft.armor is None else str(draft.armor.armor_class)),
        ("Strength", str(draft.abilities.strength)),
        ("Dexterity", str(draft.abilities.dexterity)),
        ("Constitution", str(draft.abilities.constitution)),
        ("Intelligence", str(draft.abilities.intelligence)),
        ("Wisdom", str(draft.abilities.wisdom)),
        ("Charisma", str(draft.abilities.charisma)),
        ("Skills", ", ".join(draft.skills)),
        ("Inventory", ", ".join(item.name for item in draft.inventory)),
        ("Weapons", "; ".join(_weapon_text(weapon) for weapon in draft.weapons)),
        ("Source", draft.source),
    ]


def draft_from_review_rows(rows: list[tuple[str, str]]) -> CharacterImportDraft:
    """Build a draft from edited field/value rows."""
    values = {_field_key(name): value.strip() for name, value in rows if name.strip()}
    name = values.get("name", "").strip()
    if not name:
        raise ValueError("Character name is required.")
    maximum_hp = _positive_int(values.get("maximum_hp"), "Maximum HP", default=1)
    current_hp = _positive_int(values.get("current_hp"), "Current HP", default=maximum_hp)
    temporary_hp = _nonnegative_int(values.get("temporary_hp"), "Temporary HP", default=0)
    armor_class = _optional_positive_int(values.get("armor_class"), "Armor Class")
    return CharacterImportDraft(
        name=name,
        level=_positive_int(values.get("level"), "Level", default=1),
        hit_points=HitPoints(current=current_hp, maximum=maximum_hp, temporary=temporary_hp),
        abilities=AbilityScores(
            strength=_ability_score(values.get("strength"), "Strength"),
            dexterity=_ability_score(values.get("dexterity"), "Dexterity"),
            constitution=_ability_score(values.get("constitution"), "Constitution"),
            intelligence=_ability_score(values.get("intelligence"), "Intelligence"),
            wisdom=_ability_score(values.get("wisdom"), "Wisdom"),
            charisma=_ability_score(values.get("charisma"), "Charisma"),
        ),
        skills=tuple(_split_review_list(values.get("skills", ""))),
        inventory=tuple(
            _inventory_item(name) for name in _split_review_list(values.get("inventory", ""))
        ),
        weapons=tuple(
            _parse_weapon(value) for value in _split_review_list(values.get("weapons", ""))
        ),
        armor=Armor("Imported armor", armor_class) if armor_class is not None else None,
        source=values.get("source", "pdf") or "pdf",
    )


def _populate_review_table(qt, table, rows: list[tuple[str, str]]) -> None:
    if hasattr(table, "setRowCount"):
        table.setRowCount(len(rows))
    for row, (name, value) in enumerate(rows):
        table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(name))
        table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(value))
    if hasattr(table, "resizeColumnsToContents"):
        table.resizeColumnsToContents()


def _review_buttons(qt, dialog):
    button_box = getattr(qt.QtWidgets, "QDialogButtonBox", None)
    if button_box is None:
        return None
    standard_button = getattr(button_box, "StandardButton", button_box)
    buttons = button_box(
        getattr(standard_button, "Ok", 0) | getattr(standard_button, "Cancel", 0)
    )
    if hasattr(buttons, "accepted"):
        buttons.accepted.connect(dialog.accept)
    if hasattr(buttons, "rejected"):
        buttons.rejected.connect(dialog.reject)
    return buttons


def _dialog_accepted(qt, dialog) -> bool:
    result = dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()
    dialog_code = getattr(getattr(qt.QtWidgets.QDialog, "DialogCode", None), "Accepted", None)
    if dialog_code is None:
        dialog_code = getattr(qt.QtWidgets.QDialog, "Accepted", 1)
    return result == dialog_code or result is True


def _read_review_table(table) -> list[tuple[str, str]]:
    rows = []
    for row in range(table.rowCount()):
        name_item = table.item(row, 0)
        value_item = table.item(row, 1)
        name = name_item.text() if name_item is not None else ""
        value = value_item.text() if value_item is not None else ""
        rows.append((name, value))
    return rows


def _show_review_error(qt, parent, message: str) -> None:
    message_box = getattr(qt.QtWidgets, "QMessageBox", None)
    if message_box is not None and hasattr(message_box, "warning"):
        message_box.warning(parent, "Confirm Character Import", message)


def _field_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _positive_int(value: str | None, label: str, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a whole number.") from exc
    if number < 1:
        raise ValueError(f"{label} must be at least 1.")
    return number


def _nonnegative_int(value: str | None, label: str, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a whole number.") from exc
    if number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number


def _optional_positive_int(value: str | None, label: str) -> int | None:
    if value is None or not value.strip():
        return None
    return _positive_int(value, label, 1)


def _ability_score(value: str | None, label: str) -> int:
    score = _positive_int(value, label, 10)
    if score > 30:
        raise ValueError(f"{label} must be 30 or less.")
    return score


def _split_review_list(value: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\n|,", value) if part.strip()]


def _inventory_item(name: str) -> InventoryItem:
    return InventoryItem(
        item_id=_slug(name),
        name=name,
        category=ItemCategory.OTHER,
    )


def _parse_weapon(value: str) -> Weapon:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) == 3:
        name, dice, damage_type = parts
    else:
        match = re.match(
            r"(?P<name>.+?)\s+(?P<dice>\d+d\d+(?:[+-]\d+)?)\s+(?P<damage_type>\w+)$",
            value,
            flags=re.I,
        )
        if not match:
            raise ValueError(f"Weapon must look like 'Name | 1d8 | slashing': {value}")
        name = match.group("name").strip()
        dice = match.group("dice").strip()
        damage_type = match.group("damage_type").strip()
    return Weapon(
        name=name,
        damage=DamageProfile((DamageComponent(dice.lower(), DamageType(damage_type.lower())),)),
    )


def _weapon_text(weapon: Weapon) -> str:
    component = weapon.damage.components[0]
    return f"{weapon.name} | {component.dice} | {component.damage_type.value}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "item"
