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
    CurrencyPurse,
    DamageComponent,
    DamageProfile,
    DamageType,
    HitPoints,
    InventoryItem,
    ItemCategory,
    ResourcePool,
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
        level = _extract_level(normalized)
        return CharacterImportDraft(
            name=name,
            level=level,
            hit_points=HitPoints(current=current_hp, maximum=maximum_hp, temporary=temporary_hp),
            abilities=abilities,
            skills=_extract_skills(normalized),
            inventory=_extract_inventory(normalized),
            weapons=weapons,
            armor=Armor("Imported armor", armor_class) if armor_class else None,
            currency=_extract_currency(normalized),
            resources=_extract_resources(normalized, level),
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
        text = self._extract_reader_text(reader)
        literal_text = _extract_pdf_literal_text(path.read_bytes())
        return "\n".join(part for part in (text, literal_text) if part.strip())

    def _extract_pdf_bytes(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise CharacterImportError(
                'PDF import requires pypdf. Install it with: pip install ".[pdf]"'
            ) from exc

        text = self._extract_reader_text(PdfReader(BytesIO(content)))
        literal_text = _extract_pdf_literal_text(content)
        return "\n".join(part for part in (text, literal_text) if part.strip())

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


def _extract_pdf_literal_text(content: bytes) -> str:
    values: list[str] = []
    for pattern in (rb"/V\(([^)]{1,160})\)", rb"\(([^)]{1,160})\)\s*Tj"):
        values.extend(_decode_pdf_literal(match) for match in re.findall(pattern, content))
    values = [value for value in values if _useful_pdf_literal(value)]
    labeled = _dndbeyond_labeled_text(values)
    return "\n".join((*labeled, *dict.fromkeys(values)))


def _decode_pdf_literal(value: bytes) -> str:
    text = value.decode("latin-1", errors="ignore")
    text = text.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    return re.sub(r"\s+", " ", text).strip()


def _useful_pdf_literal(value: str) -> bool:
    if not value:
        return False
    return bool(re.search(r"[A-Za-z0-9]", value))


def _dndbeyond_labeled_text(values: list[str]) -> tuple[str, ...]:
    if len(values) < 18:
        return ()
    labeled = [
        f"Character Name: {values[0]}",
        f"Class & Level: {values[1]}",
        f"Player Name: {values[2]}",
        f"Species: {values[3]}",
        f"Background: {values[4]}",
    ]
    ability_values = _dndbeyond_ability_values(values)
    if ability_values:
        names = ("Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma")
        labeled.extend(
            f"{name}: {value}" for name, value in zip(names, ability_values, strict=False)
        )
    hp = _dndbeyond_hit_points(values)
    if hp is not None:
        labeled.extend((f"Max HP: {hp}", f"Current HP: {hp}"))
    armor_class = _dndbeyond_armor_class(values)
    if armor_class is not None:
        labeled.append(f"Armor Class: {armor_class}")
    inventory = _dndbeyond_inventory_items(values)
    if inventory:
        labeled.append(f"Inventory: {'; '.join(inventory)}")
    currency = _dndbeyond_currency(values)
    if currency:
        labeled.append(f"Currency: {currency}")
    return tuple(labeled)


def _dndbeyond_ability_values(values: list[str]) -> tuple[int, ...]:
    for index in range(0, max(0, len(values) - 12)):
        possible = values[index : index + 12 : 2]
        modifiers = values[index + 1 : index + 12 : 2]
        if all(re.fullmatch(r"\d{1,2}", value) for value in possible) and all(
            re.fullmatch(r"[+-]\d+", modifier) for modifier in modifiers
        ):
            return tuple(int(value) for value in possible)
    return ()


def _dndbeyond_hit_points(values: list[str]) -> int | None:
    for index, value in enumerate(values):
        if re.fullmatch(r"\d+d\d+", value.lower()) and index >= 1:
            previous = values[index - 1]
            if re.fullmatch(r"\d{1,3}", previous):
                return int(previous)
    return None


def _dndbeyond_armor_class(values: list[str]) -> int | None:
    for index, value in enumerate(values):
        if value.lower().startswith("darkvision") and index + 1 < len(values):
            for candidate in values[index + 1 : index + 7]:
                if re.fullmatch(r"\d{1,2}", candidate):
                    armor_class = int(candidate)
                    if 10 <= armor_class <= 30:
                        return armor_class
    return None


def _dndbeyond_inventory_items(values: list[str]) -> tuple[str, ...]:
    start = next((index for index, value in enumerate(values) if value == "Bag of Holding"), None)
    if start is None:
        return ()
    items = []
    index = start
    while index < len(values):
        name = values[index]
        if index > start and name == values[0]:
            break
        if _looks_like_inventory_name(name):
            items.append(name)
            index += 3
            continue
        index += 1
    return tuple(items)


def _dndbeyond_currency(values: list[str]) -> str | None:
    for value in values:
        if re.fullmatch(r"\d[\d,]*\s*(?:pp|gp|sp|cp)", value.strip(), flags=re.I):
            return value.strip()
    return None


def _looks_like_inventory_name(value: str) -> bool:
    if re.fullmatch(r"\d[\d,]*\s*(?:pp|gp|sp|cp)", value.strip(), flags=re.I):
        return False
    return bool(re.search(r"[A-Za-z]", value)) and not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value)


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
    match = re.search(
        r"^(?:character\s*name|name)\s*:[ \t]*([A-Za-z][A-Za-z '\-]{1,60})$",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if match:
        return _restore_name_case(_clean_name(match.group(1)), text)
    label_below = _extract_value_before_label(text, "character name")
    if label_below:
        return _restore_name_case(_clean_name(label_below), text)
    match = re.search(r"^([A-Za-z][A-Za-z '\-]{1,60})$", text, flags=re.MULTILINE)
    if match:
        return _restore_name_case(_clean_name(match.group(1)), text)
    return "Imported Character"


def _clean_name(value: str) -> str:
    value = re.split(r"\s{2,}|\s+class\b|\s+level\b", value.strip(), maxsplit=1, flags=re.I)[0]
    return re.sub(
        r"\b(?:character\s*name|experience points|background)\b.*$",
        "",
        value,
        flags=re.I,
    ).strip()


def _restore_name_case(name: str, text: str) -> str:
    """Prefer an extracted occurrence that preserves the sheet's display casing."""
    if not name:
        return name
    pattern = re.compile(
        rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        candidate = match.group(0).strip()
        if _has_display_case(candidate):
            return candidate
    return name


def _has_display_case(value: str) -> bool:
    return any(character.isupper() for character in value) and any(
        character.islower() for character in value
    )


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
    match = re.search(
        r"^class\s*&\s*level\s*:?.*?\b(\d{1,2})\b",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if match:
        return max(1, int(match.group(1)))
    match = re.search(r"\blevel\s*:?\s*(\d{1,2})\b", text, flags=re.IGNORECASE)
    if match:
        return max(1, int(match.group(1)))
    match = re.search(r"\bclass(?:\s*&\s*level)?\s*:?.*?\b(\d{1,2})\b", text, flags=re.I)
    return max(1, int(match.group(1))) if match else 1


def _extract_resources(text: str, level: int) -> dict[str, ResourcePool]:
    resources: dict[str, ResourcePool] = {}
    for slot_level, maximum in _spell_slots_for_imported_character(text, level).items():
        name = f"spell_slot_{slot_level}"
        resources[name] = ResourcePool(name, maximum, maximum)
    if level > 0:
        resources["hit_dice"] = ResourcePool("hit_dice", level, level)
    return resources


def _spell_slots_for_imported_character(text: str, level: int) -> dict[int, int]:
    progression = _caster_progression(text)
    if progression is None:
        return {}
    effective_level = max(1, level)
    if progression == "half":
        effective_level = max(1, (level + 1) // 2)
    if progression == "third":
        effective_level = max(1, (level + 2) // 3)
    return _full_caster_spell_slots(effective_level)


def _caster_progression(text: str) -> str | None:
    lowered = text.lower()
    if re.search(r"\b(?:bard|cleric|druid|sorcerer|wizard)\b", lowered):
        return "full"
    if re.search(r"\b(?:paladin|ranger|artificer)\b", lowered):
        return "half"
    if re.search(r"\b(?:eldritch knight|arcane trickster)\b", lowered):
        return "third"
    if re.search(r"\b(?:cantrips?|domain spells?|spellcasting|prepared spells?)\b", lowered):
        return "full"
    return None


def _full_caster_spell_slots(level: int) -> dict[int, int]:
    slots_by_level = {
        1: (2,),
        2: (3,),
        3: (4, 2),
        4: (4, 3),
        5: (4, 3, 2),
        6: (4, 3, 3),
        7: (4, 3, 3, 1),
        8: (4, 3, 3, 2),
        9: (4, 3, 3, 3, 1),
        10: (4, 3, 3, 3, 2),
        11: (4, 3, 3, 3, 2, 1),
        12: (4, 3, 3, 3, 2, 1),
        13: (4, 3, 3, 3, 2, 1, 1),
        14: (4, 3, 3, 3, 2, 1, 1),
        15: (4, 3, 3, 3, 2, 1, 1, 1),
        16: (4, 3, 3, 3, 2, 1, 1, 1),
        17: (4, 3, 3, 3, 2, 1, 1, 1, 1),
        18: (4, 3, 3, 3, 3, 1, 1, 1, 1),
        19: (4, 3, 3, 3, 3, 2, 1, 1, 1),
        20: (4, 3, 3, 3, 3, 2, 2, 1, 1),
    }
    slots = slots_by_level[min(max(level, 1), 20)]
    return dict(enumerate(slots, start=1))


def _extract_int(text: str, labels: tuple[str, ...], default: int | None = None) -> int | None:
    for label in labels:
        line_match = re.search(
            rf"^{_plain_label_pattern(label)}\s*:?\s*(\d+)\b",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if line_match:
            return int(line_match.group(1))
        match = re.search(rf"{label}\s*:?\s*(\d+)", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return default


def _plain_label_pattern(label: str) -> str:
    plain = label.replace(r"\b", "")
    plain = plain.replace("(?:", "").replace(")?", "").replace("?", "")
    plain = plain.replace("(", "").replace(")", "")
    return plain


def _extract_abilities(text: str) -> AbilityScores:
    values = {}
    for name in CharacterImportService._ability_names:
        short = name[:3]
        value = _extract_int(text, (rf"\b{name}\b", rf"\b{short}\b"), default=10)
        values[name] = value or 10
    return AbilityScores(**values)


def _extract_skills(text: str) -> tuple[str, ...]:
    match = re.search(
        r"^skills?\s*:?\s*(.+?)(?:\n(?:inventory|equipment|weapons?|features?|"
        r"saves?|hit dice|hit points|speed|armor|class|proficiency bonus)\b|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    if not match:
        return _known_skills_in_text(text)
    candidates = _split_list(match.group(1))
    skills = _known_skills_from_candidates(candidates)
    if skills:
        return skills
    if _looks_like_noisy_skill_block(match.group(1)):
        return ()
    return tuple(name for name in candidates if name)


def _extract_currency(text: str) -> CurrencyPurse:
    labeled = re.findall(r"^currency\s*:?\s*(.+)$", text, flags=re.I | re.M)
    if labeled:
        return _currency_from_text(" ".join(labeled))
    return _currency_from_text(text)


def _currency_from_text(text: str) -> CurrencyPurse:
    total_cp = 0
    multipliers = {"pp": 1000, "gp": 100, "sp": 10, "cp": 1}
    for amount, label in re.findall(r"(\d[\d,]*)\s*(pp|gp|sp|cp)\b", text, flags=re.I):
        total_cp += int(amount.replace(",", "")) * multipliers[label.lower()]
    return CurrencyPurse.from_cp(total_cp)


def _extract_inventory(text: str) -> tuple[InventoryItem, ...]:
    line_match = re.search(r"^inventory\s*:?\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
    if line_match:
        return _inventory_items_from_names(_split_inventory_line(line_match.group(1)))
    match = re.search(
        r"\b(?:inventory|equipment)\s*:?\s*(.+?)(?:\n(?:features?|attacks?|weapons?)\b|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ()
    return _inventory_items_from_names(_split_list(match.group(1)))


def _inventory_items_from_names(names: list[str]) -> tuple[InventoryItem, ...]:
    items = []
    for name in names:
        item_id = _slug(name)
        if item_id:
            items.append(InventoryItem(item_id=item_id, name=name, category=ItemCategory.OTHER))
    return tuple(items)


def _split_inventory_line(value: str) -> list[str]:
    if ";" in value:
        return [part.strip(" .:-") for part in value.split(";") if part.strip(" .:-")]
    return _split_list(value)


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


_SKILL_DISPLAY_NAMES = {
    "acrobatics": "Acrobatics",
    "animal handling": "Animal Handling",
    "arcana": "Arcana",
    "athletics": "Athletics",
    "deception": "Deception",
    "history": "History",
    "insight": "Insight",
    "intimidation": "Intimidation",
    "investigation": "Investigation",
    "medicine": "Medicine",
    "nature": "Nature",
    "perception": "Perception",
    "performance": "Performance",
    "persuasion": "Persuasion",
    "religion": "Religion",
    "sleight of hand": "Sleight of Hand",
    "stealth": "Stealth",
    "survival": "Survival",
}


def _known_skills_from_candidates(candidates: list[str]) -> tuple[str, ...]:
    skills = []
    for candidate in candidates:
        normalized = re.sub(r"\s+", " ", candidate.lower()).strip()
        if normalized in _SKILL_DISPLAY_NAMES:
            skills.append(_SKILL_DISPLAY_NAMES[normalized])
    return tuple(dict.fromkeys(skills))


def _known_skills_in_text(text: str) -> tuple[str, ...]:
    skills = []
    for normalized, display in _SKILL_DISPLAY_NAMES.items():
        if re.search(rf"\b{re.escape(normalized)}\b", text, flags=re.I):
            skills.append(display)
    return tuple(skills)


def _looks_like_noisy_skill_block(value: str) -> bool:
    return bool(
        re.search(
            r"\b(?:saves?|hit dice|hit points|speed|armor|class|proficiency bonus|"
            r"wizards of the coast|d&d beyond)\b",
            value,
            flags=re.I,
        )
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80]
