"""Character sheet import services."""

from __future__ import annotations

import re
from pathlib import Path

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


class CharacterImportError(ValueError):
    """Raised when a character sheet cannot be imported."""


class CharacterImportService:
    """Parse uploaded character sheet files into reviewable drafts."""

    _ability_names = (
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    )

    def import_pdf(self, pdf_path: Path | str) -> CharacterImportDraft:
        """Extract a character draft from a text or fillable PDF file."""
        path = Path(pdf_path)
        if not path.exists():
            raise CharacterImportError(f"PDF not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise CharacterImportError("character import requires a PDF file")
        text = self._extract_pdf_text(path)
        return self.parse_text(text, source=str(path))

    def parse_text(self, text: str, source: str = "pdf") -> CharacterImportDraft:
        """Parse extracted character sheet text into a draft."""
        normalized = _normalize_text(text)
        name = _extract_name(normalized)
        maximum_hp = _extract_int(normalized, (r"\bmax(?:imum)? hp\b", r"\bhp maximum\b"))
        current_hp = _extract_int(normalized, (r"\bcurrent hp\b", r"\bhit points\b"))
        temporary_hp = _extract_int(normalized, (r"\btemp(?:orary)? hp\b",), default=0)
        maximum_hp = maximum_hp or current_hp or 1
        current_hp = current_hp or maximum_hp
        armor_class = _extract_int(normalized, (r"\barmor class\b", r"\bac\b"))
        abilities = _extract_abilities(normalized)
        weapons = _extract_weapons(normalized)
        return CharacterImportDraft(
            name=name,
            level=_extract_level(normalized),
            hit_points=HitPoints(current=current_hp, maximum=maximum_hp, temporary=temporary_hp),
            abilities=abilities,
            skills=_extract_skills(normalized),
            inventory=_extract_inventory(normalized),
            weapons=weapons,
            armor=Armor("Imported armor", armor_class) if armor_class else None,
            source=source,
        )

    def _extract_pdf_text(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise CharacterImportError(
                'PDF import requires pypdf. Install it with: pip install ".[pdf]"'
            ) from exc

        reader = PdfReader(str(path))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        fields = reader.get_fields() or {}
        for name, field in fields.items():
            value = _field_value(field)
            if value:
                text_parts.append(f"{name}: {value}")
        text = "\n".join(part for part in text_parts if part)
        if not text.strip():
            raise CharacterImportError("no readable text or form fields found in PDF")
        return text


def _normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\r", "\n").splitlines() if line.strip())


def _field_value(field: object) -> str:
    if isinstance(field, dict):
        value = field.get("/V") or field.get("V")
        return "" if value is None else str(value)
    value = getattr(field, "value", None)
    return "" if value is None else str(value)


def _extract_name(text: str) -> str:
    patterns = (
        r"(?:character\s*name|name)\s*:?\s*([A-Za-z][A-Za-z '\-]{1,60})",
        r"^([A-Za-z][A-Za-z '\-]{1,60})$",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _clean_name(match.group(1))
    return "Imported Character"


def _clean_name(value: str) -> str:
    return re.split(r"\s{2,}|\s+class\b|\s+level\b", value.strip(), maxsplit=1, flags=re.I)[0]


def _extract_level(text: str) -> int:
    match = re.search(r"\blevel\s*:?\s*(\d{1,2})\b", text, flags=re.IGNORECASE)
    if match:
        return max(1, int(match.group(1)))
    match = re.search(r"\bclass(?:\s*&\s*level)?\s*:?.*?\b(\d{1,2})\b", text, flags=re.I)
    return max(1, int(match.group(1))) if match else 1


def _extract_int(text: str, labels: tuple[str, ...], default: int | None = None) -> int | None:
    for label in labels:
        match = re.search(rf"{label}\s*:?\s*(\d+)", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return default


def _extract_abilities(text: str) -> AbilityScores:
    values = {}
    for name in CharacterImportService._ability_names:
        short = name[:3]
        value = _extract_int(text, (rf"\b{name}\b", rf"\b{short}\b"), default=10)
        values[name] = value or 10
    return AbilityScores(**values)


def _extract_skills(text: str) -> tuple[str, ...]:
    match = re.search(
        r"\bskills?\s*:?\s*(.+?)(?:\n(?:inventory|equipment|weapons?|features?)\b|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ()
    names = _split_list(match.group(1))
    return tuple(name for name in names if name)


def _extract_inventory(text: str) -> tuple[InventoryItem, ...]:
    match = re.search(
        r"\b(?:inventory|equipment)\s*:?\s*(.+?)(?:\n(?:features?|attacks?|weapons?)\b|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ()
    items = []
    for name in _split_list(match.group(1)):
        item_id = _slug(name)
        if item_id:
            items.append(InventoryItem(item_id=item_id, name=name, category=ItemCategory.OTHER))
    return tuple(items)


def _extract_weapons(text: str) -> tuple[Weapon, ...]:
    damage_types = "|".join(item.value for item in DamageType)
    pattern = re.compile(
        rf"(?P<name>[A-Za-z][A-Za-z '\-]{{1,40}}?)\s+"
        rf"(?:[+-]\d+\s+)?"
        rf"(?P<dice>\d+d\d+(?:[+-]\d+)?)\s*"
        rf"(?P<damage_type>{damage_types})\b",
        flags=re.IGNORECASE,
    )
    weapons = []
    for match in pattern.finditer(text):
        name = match.group("name").strip(" :-")
        dice = match.group("dice").lower()
        damage_type = DamageType(match.group("damage_type").lower())
        weapons.append(
            Weapon(
                name=name,
                damage=DamageProfile((DamageComponent(dice, damage_type),)),
            )
        )
    return tuple(weapons)


def _split_list(value: str) -> list[str]:
    parts = re.split(r",|;|\n", value)
    return [part.strip(" .:-") for part in parts if part.strip(" .:-")]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80]

