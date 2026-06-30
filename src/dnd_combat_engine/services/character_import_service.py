"""Character sheet import services."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from html import unescape
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

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


@dataclass(frozen=True, slots=True)
class _UrlPayload:
    content: bytes
    content_type: str
    final_url: str


class CharacterImportService:
    """Parse uploaded character sheet files into reviewable drafts."""

    max_url_bytes = 5_000_000
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

    def import_url(self, url: str) -> CharacterImportDraft:
        """Extract a character draft from a public PDF, HTML, or text URL."""
        payload = self._fetch_url(url)
        if _looks_like_pdf(payload):
            text = self._extract_pdf_bytes(payload.content)
        else:
            text = _extract_url_text(payload)
        return self.parse_text(text, source=payload.final_url)

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
        return self._extract_reader_text(reader)

    def _extract_pdf_bytes(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise CharacterImportError(
                'PDF import requires pypdf. Install it with: pip install ".[pdf]"'
            ) from exc

        return self._extract_reader_text(PdfReader(BytesIO(content)))

    def _extract_reader_text(self, reader) -> str:
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

    def _fetch_url(self, url: str) -> _UrlPayload:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise CharacterImportError("character URL must be an http or https URL")
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "DnDCombatEngine/0.1 character-import",
                "Accept": "application/pdf,text/html,text/plain;q=0.9,*/*;q=0.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                content = response.read(self.max_url_bytes + 1)
                content_type = response.headers.get("Content-Type", "")
                final_url = response.geturl()
        except urllib.error.URLError as exc:
            raise CharacterImportError(f"could not read character URL: {exc}") from exc
        if len(content) > self.max_url_bytes:
            raise CharacterImportError("character URL response is too large")
        if not content:
            raise CharacterImportError("character URL returned no content")
        return _UrlPayload(content=content, content_type=content_type, final_url=final_url)


def _normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\r", "\n").splitlines() if line.strip())


def _field_value(field: object) -> str:
    if isinstance(field, dict):
        value = field.get("/V") or field.get("V")
        return "" if value is None else str(value)
    value = getattr(field, "value", None)
    return "" if value is None else str(value)


def _looks_like_pdf(payload: _UrlPayload) -> bool:
    return (
        "application/pdf" in payload.content_type.lower()
        or urlparse(payload.final_url).path.lower().endswith(".pdf")
        or payload.content.startswith(b"%PDF")
    )


def _extract_url_text(payload: _UrlPayload) -> str:
    content_type = payload.content_type.lower()
    if "html" not in content_type and "text" not in content_type and content_type:
        raise CharacterImportError("character URL must point to a PDF, HTML, or text page")
    text = payload.content.decode(_charset_from_content_type(content_type), errors="replace")
    if "html" in content_type or "<html" in text[:500].lower():
        text = _html_to_text(text)
    if not text.strip():
        raise CharacterImportError("character URL contained no readable text")
    return text


def _charset_from_content_type(content_type: str) -> str:
    match = re.search(r"charset=([\w\-]+)", content_type)
    return match.group(1) if match else "utf-8"


def _html_to_text(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"</(?:p|div|li|tr|h[1-6])>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return unescape(re.sub(r"[ \t]+", " ", value))


def _extract_name(text: str) -> str:
    label_below = _extract_value_before_label(text, "character name")
    if label_below:
        return _clean_name(label_below)
    patterns = (
        r"^(?:character\s*name|name)\s*:?[ \t]*([A-Za-z][A-Za-z '\-]{1,60})$",
        r"^([A-Za-z][A-Za-z '\-]{1,60})$",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _clean_name(match.group(1))
    return "Imported Character"


def _clean_name(value: str) -> str:
    value = re.split(r"\s{2,}|\s+class\b|\s+level\b", value.strip(), maxsplit=1, flags=re.I)[0]
    return re.sub(
        r"\b(?:character\s*name|experience points|background)\b.*$",
        "",
        value,
        flags=re.I,
    ).strip()


def _extract_value_before_label(text: str, label: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    label_pattern = re.compile(rf"^{label}$", flags=re.IGNORECASE)
    for index, line in enumerate(lines):
        if label_pattern.match(line) and index > 0:
            value = lines[index - 1].strip()
            if _looks_like_character_name(value):
                return value
    return None


def _looks_like_character_name(value: str) -> bool:
    if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]{1,60}", value):
        return False
    labels = {
        "background",
        "character name",
        "class",
        "class & level",
        "experience points",
        "player name",
        "species",
    }
    return value.lower() not in labels


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
