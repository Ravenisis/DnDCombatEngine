"""Character sheet import services."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from html import unescape
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

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
            return self.parse_text(text, source=payload.final_url)
        dndbeyond_pdf_url = _dndbeyond_sheet_pdf_url(payload)
        if dndbeyond_pdf_url is not None:
            pdf_payload = self._fetch_url(dndbeyond_pdf_url)
            if not _looks_like_pdf(pdf_payload):
                raise CharacterImportError(
                    "D&D Beyond character page linked a sheet export, but it was not a PDF"
                )
            text = self._extract_pdf_bytes(pdf_payload.content)
            return self.parse_text(text, source=pdf_payload.final_url)
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
        character_class = _extract_character_class(normalized)
        race = _extract_race(normalized)
        proficiency_bonus = _extract_proficiency_bonus(normalized, level)
        spellcasting_ability = _extract_spellcasting_ability(normalized)
        saving_throw_proficiencies = _extract_saving_throw_proficiencies(normalized)
        saving_throw_modifiers = _extract_saving_throw_modifiers(
            normalized,
            abilities,
            saving_throw_proficiencies,
            proficiency_bonus,
        )
        return CharacterImportDraft(
            name=name,
            level=level,
            hit_points=HitPoints(current=current_hp, maximum=maximum_hp, temporary=temporary_hp),
            abilities=abilities,
            character_class=character_class,
            race=race,
            senses=_extract_senses(normalized),
            initiative_modifier=_extract_initiative_modifier(normalized, abilities),
            heroic_inspiration=_extract_heroic_inspiration(normalized),
            proficiency_bonus=proficiency_bonus,
            ability_save_dc=_extract_ability_save_dc(normalized, abilities, proficiency_bonus),
            walking_speed=_extract_walking_speed(normalized),
            spellcasting_ability=spellcasting_ability,
            spell_save_dc=_extract_spell_save_dc(
                normalized,
                abilities,
                proficiency_bonus,
                spellcasting_ability,
            ),
            spell_attack_bonus=_extract_spell_attack_bonus(
                normalized,
                abilities,
                proficiency_bonus,
                spellcasting_ability,
            ),
            saving_throw_modifiers=saving_throw_modifiers,
            skills=_extract_skills(normalized),
            inventory=_extract_inventory(normalized),
            weapons=weapons,
            armor=Armor("Imported armor", armor_class) if armor_class else None,
            features=_extract_features(normalized),
            spells=_extract_spells(normalized),
            currency=_extract_currency(normalized),
            resources=_extract_resources(normalized, level),
            saving_throw_proficiencies=saving_throw_proficiencies,
            armor_proficiencies=_extract_named_proficiency_block(normalized, "armor"),
            weapon_proficiencies=_extract_named_proficiency_block(normalized, "weapons"),
            tool_proficiencies=_extract_named_proficiency_block(normalized, "tools"),
            languages=_extract_named_proficiency_block(normalized, "languages"),
            damage_resistances=_extract_damage_resistances(normalized),
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


def _dndbeyond_sheet_pdf_url(payload: _UrlPayload) -> str | None:
    """Return a linked D&D Beyond sheet PDF URL when a character page exposes one."""
    if not _looks_like_dndbeyond_character_page(payload):
        return None
    html = _decode_payload_text(payload)
    if not html.strip():
        return None
    candidates = _sheet_pdf_candidates(html)
    return urljoin(payload.final_url, candidates[0]) if candidates else None


def _looks_like_dndbeyond_character_page(payload: _UrlPayload) -> bool:
    parsed = urlparse(payload.final_url)
    host = parsed.netloc.lower()
    return host.endswith("dndbeyond.com") and bool(
        re.search(r"/(?:characters|profile/[^/]+/characters)/\d+\b", parsed.path)
    )


def _decode_payload_text(payload: _UrlPayload) -> str:
    content_type = payload.content_type.lower()
    return payload.content.decode(_charset_from_content_type(content_type), errors="replace")


def _sheet_pdf_candidates(html: str) -> tuple[str, ...]:
    normalized = (
        unescape(html)
        .replace(r"\\/", "/")
        .replace(r"\/", "/")
        .replace(r"\\u002F", "/")
        .replace(r"\u002F", "/")
    )
    candidates: list[str] = []
    patterns = (
        r"https?://[^\"'<>\s]+/sheet-pdfs/[^\"'<>\s]+?\.pdf(?:\?[^\"'<>\s]*)?",
        r"(?P<url>/sheet-pdfs/[^\"'<>\s]+?\.pdf(?:\?[^\"'<>\s]*)?)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized, flags=re.I):
            candidate = match.groupdict().get("url") or match.group(0)
            candidates.append(candidate.strip())
    return tuple(dict.fromkeys(candidates))


def _extract_url_text(payload: _UrlPayload) -> str:
    content_type = payload.content_type.lower()
    if "html" not in content_type and "text" not in content_type and content_type:
        raise CharacterImportError("character URL must point to a PDF, HTML, or text page")
    text = _decode_payload_text(payload)
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
    senses = _dndbeyond_senses(values)
    if senses:
        labeled.append(f"Senses: {senses}")
    proficiency_bonus = _dndbeyond_proficiency_bonus(values)
    if proficiency_bonus is not None:
        labeled.append(f"Proficiency Bonus: {proficiency_bonus:+d}")
    walking_speed = _dndbeyond_walking_speed(values)
    if walking_speed is not None:
        labeled.append(f"Walking Speed: {walking_speed} ft.")
    spellcasting = _dndbeyond_spellcasting_stats(values)
    if spellcasting:
        labeled.extend(spellcasting)
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


def _dndbeyond_senses(values: list[str]) -> str:
    for value in values:
        if not re.search(r"\bdarkvision\s+\d+\s*ft\.?", value, flags=re.I):
            continue
        sense = _normalize_sense(value)
        if sense:
            return sense
    return ""


def _dndbeyond_proficiency_bonus(values: list[str]) -> int | None:
    for index, value in enumerate(values[:-1]):
        if re.fullmatch(r"darkvision\s+\d+\s*ft\.?", value, flags=re.I):
            window = values[index + 1 : index + 8]
            for candidate_index, candidate in enumerate(window[:-1]):
                if not re.fullmatch(r"\d{1,2}", candidate):
                    continue
                armor_class = int(candidate)
                if 10 <= armor_class <= 30:
                    for signed in window[candidate_index + 1 :]:
                        if re.fullmatch(r"[+-]\d+", signed):
                            return int(signed)
    return None


def _dndbeyond_walking_speed(values: list[str]) -> int | None:
    for index, value in enumerate(values[:-1]):
        if not re.fullmatch(r"darkvision\s+\d+\s*ft\.?", value, flags=re.I):
            continue
        window = values[index + 1 : index + 8]
        saw_armor_class = False
        saw_proficiency = False
        for candidate in window:
            if not saw_armor_class and re.fullmatch(r"\d{1,2}", candidate):
                armor_class = int(candidate)
                if 10 <= armor_class <= 30:
                    saw_armor_class = True
                continue
            if saw_armor_class and not saw_proficiency and re.fullmatch(r"[+-]\d+", candidate):
                saw_proficiency = True
                continue
            if saw_proficiency:
                match = re.search(r"\b(\d+)\s*ft\.?", candidate, flags=re.I)
                if match:
                    return int(match.group(1))
    for value in values:
        speed = _speed_from_text(value)
        if speed is not None:
            return speed
    return None


def _dndbeyond_spellcasting_stats(values: list[str]) -> tuple[str, ...]:
    labels: list[str] = []
    for index, value in enumerate(values):
        if value.lower() != "cleric":
            continue
        window = values[index + 1 : index + 16]
        joined = " ".join(window)
        dc_match = re.search(r"\bspell\s+dc\s+(\d+)\b", joined, flags=re.I)
        attack_match = re.search(r"\bspell\s+attack\s+([+-]?\d+)\b", joined, flags=re.I)
        labels.append("Spellcasting Ability: Wisdom")
        if dc_match:
            labels.append(f"Spell Save DC: {dc_match.group(1)}")
        if attack_match:
            labels.append(f"Spell Attack Bonus: {int(attack_match.group(1)):+d}")
        break
    return tuple(labels)


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
            quantity = values[index + 1] if index + 1 < len(values) else "1"
            weight = values[index + 2] if index + 2 < len(values) else "0"
            items.append(_inventory_entry_text(name, quantity, weight))
            index += 3
            continue
        index += 1
    return tuple(items)


def _inventory_entry_text(name: str, quantity: str, weight: str) -> str:
    clean_name = _repair_inventory_name(name)
    clean_quantity = quantity if re.fullmatch(r"\d+", quantity.strip()) else "1"
    weight_match = re.search(r"\d+(?:\.\d+)?", weight)
    clean_weight = weight_match.group(0) if weight_match else "0"
    return f"{clean_quantity} x {clean_name} ({clean_weight} lb)"


def _repair_inventory_name(name: str) -> str:
    clean_name = name.strip().replace(r"\(", "(").replace(r"\)", ")")
    if clean_name.count("(") > clean_name.count(")"):
        clean_name += ")"
    return clean_name


def _dndbeyond_currency(values: list[str]) -> str | None:
    for value in values:
        if re.fullmatch(r"\d[\d,]*\s*(?:pp|gp|sp|cp)", value.strip(), flags=re.I):
            return value.strip()
    for index in range(0, max(0, len(values) - 5)):
        possible = values[index : index + 5]
        if all(re.fullmatch(r"\d[\d,]*", value) for value in possible):
            cp, _ep, pp, gp, sp = possible
            if any(value != "0" for value in (cp, pp, gp, sp)):
                return f"{pp}PP {gp}GP {sp}SP {cp}CP"
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
    label_above = _extract_value_after_label(text, "character name")
    if label_above:
        return _restore_name_case(_clean_name(label_above), text)
    match = re.search(r"^([A-Za-z][A-Za-z '\-]{1,60})$", text, flags=re.MULTILINE)
    if match and _looks_like_character_name(match.group(1)):
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


def _extract_value_after_label(text: str, label: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    label_pattern = re.compile(rf"^{label}$", flags=re.IGNORECASE)
    for index, line in enumerate(lines[:-1]):
        if label_pattern.match(line):
            value = lines[index + 1].strip()
            if _looks_like_character_name(value):
                return value
    return None


def _looks_like_character_name(value: str) -> bool:
    if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]{1,60}", value):
        return False
    if re.search(r"\b(?:pdf|machine-readable|sheet|page)\b", value, flags=re.I):
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


def _extract_character_class(text: str) -> str:
    return (
        _extract_labeled_line(text, "class & level")
        or _extract_labeled_line(text, "class")
        or ""
    )


def _extract_race(text: str) -> str:
    return (
        _extract_labeled_line(text, "species/race")
        or _extract_labeled_line(text, "species")
        or _extract_labeled_line(text, "race")
        or ""
    )


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


def _extract_optional_int_label(text: str, labels: tuple[str, ...]) -> int | None:
    return _extract_int(text, labels)


def _extract_signed_label(text: str, labels: tuple[str, ...]) -> int | None:
    for label in labels:
        line_match = re.search(
            rf"^{_plain_label_pattern(label)}\s*:?\s*([+-]?\d+)\b",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if line_match:
            return int(line_match.group(1))
        match = re.search(rf"{label}\s*:?\s*([+-]?\d+)", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


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


def _extract_senses(text: str) -> tuple[str, ...]:
    labeled = _extract_labeled_line(text, "senses")
    values = [_normalize_sense(value) for value in _split_list(labeled)] if labeled else []
    values.extend(
        _normalize_sense(match.group(0))
        for match in re.finditer(r"\bdarkvision\s+\d+\s*ft\.?", text, flags=re.I)
    )
    return tuple(dict.fromkeys(value for value in values if value))


def _normalize_sense(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    match = re.search(r"\bdarkvision\s+(\d+)\s*ft\.?", normalized, flags=re.I)
    if match:
        return f"Darkvision {match.group(1)} ft."
    return normalized


def _extract_initiative_modifier(text: str, abilities: AbilityScores) -> int:
    value = _extract_signed_label(text, ("initiative",))
    return abilities.modifier("dexterity") if value is None else value


def _extract_heroic_inspiration(text: str) -> bool:
    value = _extract_labeled_line(text, "heroic inspiration")
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "checked", "x"}


def _extract_proficiency_bonus(text: str, level: int) -> int:
    value = _extract_signed_label(text, ("proficiency bonus",))
    return 2 + max(level - 1, 0) // 4 if value is None else value


def _extract_walking_speed(text: str) -> int | None:
    for label in ("walking speed", "walk speed", "speed"):
        match = re.search(rf"^{label}\s*:?\s*(\d+)\s*(?:ft\.?|feet)?", text, re.I | re.M)
        if match:
            return int(match.group(1))
    speed = _speed_from_text(text)
    if speed is not None:
        return speed
    return None


def _speed_from_text(value: str) -> int | None:
    match = re.search(r"\b(\d+)\s*ft\.?\s*(?:\(?\s*walking|walk|speed)\b", value, re.I)
    return int(match.group(1)) if match else None


def _extract_spellcasting_ability(text: str) -> str:
    value = _extract_labeled_line(text, "spellcasting ability")
    if value:
        return value
    if _is_cleric_sheet(text):
        return "Wisdom"
    return ""


def _extract_ability_save_dc(
    text: str,
    abilities: AbilityScores,
    proficiency_bonus: int,
) -> int | None:
    value = _extract_optional_int_label(text, ("ability save dc",))
    if value is not None:
        return value
    if _is_cleric_sheet(text):
        return 8 + proficiency_bonus + abilities.modifier("wisdom")
    return None


def _extract_spell_save_dc(
    text: str,
    abilities: AbilityScores,
    proficiency_bonus: int,
    spellcasting_ability: str,
) -> int | None:
    value = _extract_optional_int_label(text, ("spell save dc", "spell dc"))
    if value is not None:
        return value
    ability_name = _ability_key(spellcasting_ability)
    if ability_name:
        return 8 + proficiency_bonus + abilities.modifier(ability_name)
    return None


def _extract_spell_attack_bonus(
    text: str,
    abilities: AbilityScores,
    proficiency_bonus: int,
    spellcasting_ability: str,
) -> int | None:
    value = _extract_signed_label(text, ("spell attack bonus", "spell attack"))
    if value is not None:
        return value
    ability_name = _ability_key(spellcasting_ability)
    if ability_name:
        return proficiency_bonus + abilities.modifier(ability_name)
    return None


def _ability_key(value: str) -> str:
    display = _ability_display_name(value)
    return display.lower() if display else ""


def _extract_saving_throw_modifiers(
    text: str,
    abilities: AbilityScores,
    proficiencies: tuple[str, ...],
    proficiency_bonus: int,
) -> dict[str, int]:
    machine_readable = _extract_machine_readable_saving_throw_modifiers(text)
    if machine_readable:
        return machine_readable
    modifiers: dict[str, int] = {}
    for ability in CharacterImportService._ability_names:
        patterns = (
            rf"{ability}\s+sav(?:e|ing throw)?",
            rf"{ability[:3]}\s+sav(?:e|ing throw)?",
        )
        value = _extract_signed_label(text, patterns)
        if value is not None:
            modifiers[ability] = value
    if modifiers:
        return modifiers
    proficient = {value.lower() for value in proficiencies}
    return {
        ability: abilities.modifier(ability) + (proficiency_bonus if ability in proficient else 0)
        for ability in CharacterImportService._ability_names
    }
    return modifiers


def _extract_skills(text: str) -> tuple[str, ...]:
    proficient = _extract_machine_readable_skill_proficiencies(text)
    if proficient:
        return proficient
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


def _extract_machine_readable_skill_proficiencies(text: str) -> tuple[str, ...]:
    match = re.search(
        r"^Skill\s*$\n^Bonus\s*$\n^Proficient\s*$\n^Ability\s*$\n(.+?)(?:\n[^\n]*machine-readable|\nWeapons,|\nACTIONS\b|\Z)",
        text,
        flags=re.I | re.M | re.S,
    )
    if not match:
        return ()
    lines = _clean_lines(match.group(1))
    skills = []
    index = 0
    while index + 3 < len(lines):
        name, _bonus, proficient, _ability = lines[index : index + 4]
        display = _SKILL_DISPLAY_NAMES.get(name.lower())
        if display and proficient.lower() == "yes":
            skills.append(display)
        index += 4
    return tuple(dict.fromkeys(skills))


def _extract_saving_throw_proficiencies(text: str) -> tuple[str, ...]:
    match = re.search(
        r"^Saving Throw\s*$\n^Bonus\s*$\n^Proficient\s*$\n(.+?)(?:\nSkill\s*$|\Z)",
        text,
        flags=re.I | re.M | re.S,
    )
    if not match:
        if _is_cleric_sheet(text):
            return ("Wisdom", "Charisma")
        return ()
    lines = _clean_lines(match.group(1))
    proficiencies = []
    index = 0
    while index + 2 < len(lines):
        ability, _bonus, proficient = lines[index : index + 3]
        display = _ability_display_name(ability)
        if display and proficient.lower() == "yes":
            proficiencies.append(display)
        index += 3
    return tuple(dict.fromkeys(proficiencies))


def _extract_machine_readable_saving_throw_modifiers(text: str) -> dict[str, int]:
    match = re.search(
        r"^Saving Throw\s*$\n^Bonus\s*$\n^Proficient\s*$\n(.+?)(?:\nSkill\s*$|\Z)",
        text,
        flags=re.I | re.M | re.S,
    )
    if not match:
        return {}
    lines = _clean_lines(match.group(1))
    modifiers: dict[str, int] = {}
    index = 0
    while index + 2 < len(lines):
        ability, bonus, _proficient = lines[index : index + 3]
        display = _ability_display_name(ability)
        if display and re.fullmatch(r"[+-]?\d+", bonus):
            modifiers[display.lower()] = int(bonus)
        index += 3
    return modifiers


def _extract_currency(text: str) -> CurrencyPurse:
    machine_readable = _extract_machine_readable_currency(text)
    if machine_readable is not None:
        return machine_readable
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


def _extract_machine_readable_currency(text: str) -> CurrencyPurse | None:
    lines = _clean_lines(text)
    values: dict[str, int] = {}
    for index, line in enumerate(lines[:-1]):
        label = line.lower()
        if label in {"cp", "sp", "gp", "pp"} and re.fullmatch(r"\d[\d,]*", lines[index + 1]):
            values[label] = int(lines[index + 1].replace(",", ""))
    if not values:
        return None
    return CurrencyPurse.from_dict(values)


def _extract_inventory(text: str) -> tuple[InventoryItem, ...]:
    line_match = re.search(r"^inventory\s*:?\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
    if line_match:
        return _inventory_items_from_names(_split_inventory_line(line_match.group(1)))
    table_items = _extract_machine_readable_inventory(text)
    if table_items:
        return table_items
    match = re.search(
        r"\b(?:inventory|equipment)\s*:?\s*(.+?)(?:\n(?:features?|attacks?|weapons?)\b|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ()
    return _inventory_items_from_names(_split_list(match.group(1)))


def _extract_machine_readable_inventory(text: str) -> tuple[InventoryItem, ...]:
    items: list[InventoryItem] = []
    header = re.compile(r"^Item\s*\nQty\s*\nWeight\s*$", flags=re.I | re.M)
    for match in header.finditer(text):
        block = text[match.end() :]
        block = re.split(
            r"\n(?:[A-Za-z].*machine-readable.*|Page\s+\d+|Features and Traits|Spellcasting)\b",
            block,
            maxsplit=1,
            flags=re.I,
        )[0]
        lines = _clean_lines(block)
        index = 0
        while index < len(lines):
            name = lines[index]
            if not _looks_like_inventory_name(name):
                index += 1
                continue
            if index + 1 >= len(lines) or not re.fullmatch(r"\d+", lines[index + 1]):
                index += 1
                continue
            quantity = lines[index + 1]
            weight = "0"
            index += 2
            if index < len(lines) and re.fullmatch(r"\d+(?:\.\d+)?\s*lb\.?", lines[index], re.I):
                weight = lines[index]
                index += 1
            parsed_name, parsed_quantity, parsed_weight = _parse_inventory_entry(
                _inventory_entry_text(name, quantity, weight)
            )
            items.append(
                _enrich_imported_item(
                    parsed_name,
                    _slug(parsed_name),
                    parsed_quantity,
                    parsed_weight,
                )
            )
    return tuple(items)


def _inventory_items_from_names(names: list[str]) -> tuple[InventoryItem, ...]:
    items = []
    for raw_name in names:
        name, quantity, weight = _parse_inventory_entry(raw_name)
        item_id = _slug(name)
        if item_id:
            items.append(_enrich_imported_item(name, item_id, quantity, weight))
    return tuple(items)


def _enrich_imported_item(name: str, item_id: str, quantity: int, weight: float) -> InventoryItem:
    """Apply bundled SRD metadata to an imported item when names match."""
    catalog_item = _srd_inventory_catalog().get(_normalized_item_name(name))
    if catalog_item is None:
        return InventoryItem(
            item_id=item_id,
            name=name,
            quantity=quantity,
            weight=weight,
            category=ItemCategory.OTHER,
        )
    catalog_weight = float(catalog_item.get("weight", 0.0) or 0.0)
    return InventoryItem(
        item_id=str(catalog_item.get("item_id", item_id)),
        name=name,
        quantity=quantity,
        weight=weight or catalog_weight,
        category=ItemCategory(str(catalog_item.get("category", ItemCategory.OTHER.value))),
        notes=str(catalog_item["notes"]) if catalog_item.get("notes") else None,
        tags=tuple(str(tag) for tag in catalog_item.get("tags", [])),
        purchase_price_cp=int(catalog_item.get("purchase_price_cp", 0) or 0),
    )


@lru_cache(maxsize=1)
def _srd_inventory_catalog() -> dict[str, dict[str, object]]:
    """Load the bundled SRD item catalog once per importer process."""
    path = Path(__file__).resolve().parents[1] / "data" / "equipment" / "srd_equipment.json"
    try:
        raw_items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {
        _normalized_item_name(str(item.get("name", ""))): item
        for item in raw_items
        if isinstance(item, dict) and item.get("name")
    }


def _normalized_item_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _parse_inventory_entry(value: str) -> tuple[str, int, float]:
    text = value.strip()
    quantity = 1
    weight = 0.0
    quantity_match = re.match(r"(?P<quantity>\d+)\s*x\s+(?P<name>.+)", text, flags=re.I)
    if quantity_match:
        quantity = max(int(quantity_match.group("quantity")), 1)
        text = quantity_match.group("name").strip()
    weight_match = re.search(r"\((?P<weight>\d+(?:\.\d+)?)\s*lb\.?\)$", text, flags=re.I)
    if weight_match:
        weight = float(weight_match.group("weight"))
        text = text[: weight_match.start()].strip()
    return _repair_inventory_name(text.strip(" .:-")), quantity, weight


def _split_inventory_line(value: str) -> list[str]:
    if ";" in value:
        return [part.strip(" .:-") for part in value.split(";") if part.strip(" .:-")]
    protected = _protect_comma_item_names(value)
    return [
        _restore_protected_commas(part.strip(" .:-"))
        for part in re.split(r",|\n", protected)
        if part.strip(" .:-")
    ]


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
        if not _looks_like_weapon_name(name):
            continue
        dice = match.group("dice").lower()
        damage_type = DamageType(match.group("damage_type").lower())
        weapons.append(
            Weapon(
                name=name,
                damage=DamageProfile((DamageComponent(dice, damage_type),)),
            )
        )
    return tuple(weapons)


def _looks_like_weapon_name(name: str) -> bool:
    cleaned = name.strip().casefold()
    rejected = {
        "instead",
        "range",
        "reach",
        "notes",
        "attack",
        "attacks",
        "damage",
        "hit",
        "hit dc",
        "hit/dc",
        "dc",
    }
    return bool(cleaned) and cleaned not in rejected


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

_ABILITY_DISPLAY_NAMES = {
    "strength": "Strength",
    "dexterity": "Dexterity",
    "constitution": "Constitution",
    "intelligence": "Intelligence",
    "wisdom": "Wisdom",
    "charisma": "Charisma",
}

_ABILITY_SHORT_NAMES = {
    "str": "Strength",
    "dex": "Dexterity",
    "con": "Constitution",
    "int": "Intelligence",
    "wis": "Wisdom",
    "cha": "Charisma",
}

_COMMA_ITEM_NAMES = (
    "Clothes, Common",
    "Clothes, Costume",
    "Clothes, Fine",
    "Clothes, Traveler's",
)

_KNOWN_IMPORT_SPELLS = (
    "Beacon of Hope",
    "Bless",
    "Cure Wounds",
    "Guiding Bolt",
    "Hex",
    "Lesser Restoration",
    "Light",
    "Revivify",
    "Sacred Flame",
    "Spiritual Weapon",
    "Thaumaturgy",
)


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
            r"passive insight|passive investigation|wizards of the coast|d&d beyond)\b",
            value,
            flags=re.I,
        )
    )


def _extract_named_proficiency_block(text: str, heading: str) -> tuple[str, ...]:
    block = _extract_equals_heading_block(text, heading)
    if block:
        return _repair_proficiency_values(
            _split_proficiency_values(block),
            heading,
            text,
        )
    wrapped = _extract_wrapped_proficiency_block(text, heading)
    known = _known_proficiency_values_in_text(text, heading)
    return _repair_proficiency_values((*wrapped, *known), heading, text)


def _extract_equals_heading_block(text: str, heading: str) -> str:
    match = re.search(
        rf"^===\s*{re.escape(heading)}\s*===\s*\n(.+?)"
        r"(?:\n===|\n\s*Item\b|\nFeatures and Traits\b|\Z)",
        text,
        flags=re.I | re.M | re.S,
    )
    return match.group(1).strip() if match else ""


def _extract_wrapped_proficiency_block(text: str, heading: str) -> tuple[str, ...]:
    match = re.search(
        rf"^{re.escape(heading)}\s*\n(.+?)(?:\n(?:armor|weapons?|tools|languages|actions|special)\b|$)",
        text,
        flags=re.I | re.M | re.S,
    )
    if not match:
        return ()
    normalized = " ".join(_clean_lines(match.group(1)))
    if _looks_like_noisy_proficiency_block(normalized):
        return ()
    if heading.lower() == "tools":
        names = []
        for pattern, display in (
            (r"cook'?s\s+utensils", "Cook's Utensils"),
            (r"mason'?s\s+tools", "Mason's Tools"),
            (r"vehicles?(?:\s*\(land\))?|\bvehicles\b", "Vehicles (Land)"),
            (r"thieves'? tools", "Thieves' Tools"),
        ):
            if re.search(pattern, normalized, flags=re.I):
                names.append(display)
        return tuple(dict.fromkeys(names))
    return _split_proficiency_values(normalized)


def _looks_like_noisy_proficiency_block(value: str) -> bool:
    return bool(re.search(r"\b(?:class|hit points|speed|death saves|tm|d&d beyond)\b", value, re.I))


def _known_proficiency_values_in_text(text: str, heading: str) -> tuple[str, ...]:
    lowered = text.lower()
    if heading == "armor":
        candidates = ("Heavy Armor", "Light Armor", "Medium Armor", "Plate", "Shields")
    elif heading == "weapons":
        candidates = ("Battleaxe", "Handaxe", "Simple Weapons", "Warhammer")
    elif heading == "tools":
        candidates = ("Cook's Utensils", "Mason's Tools", "Thieves' Tools")
    elif heading == "languages":
        if not re.search(r"\blanguages?\b", lowered):
            return ()
        candidates = ("Common", "Dwarvish")
    else:
        candidates = ()
    found = []
    for candidate in candidates:
        pattern = re.escape(candidate.lower()).replace(r"\ ", r"\s+")
        if re.search(rf"\b{pattern}\b", lowered):
            found.append(candidate)
    if heading == "tools" and re.search(r"\bvehicles?(?:\s*\(land\))?\b", lowered):
        found.append("Vehicles (Land)")
    return tuple(found)


def _repair_proficiency_values(
    values: tuple[str, ...],
    heading: str,
    text: str,
) -> tuple[str, ...]:
    repaired = list(values)
    if heading == "armor" and _is_cleric_sheet(text):
        repaired.extend(("Light Armor", "Medium Armor", "Shields"))
        return _ordered_armor_proficiencies(tuple(dict.fromkeys(repaired)))
    return tuple(dict.fromkeys(repaired))


def _ordered_armor_proficiencies(values: tuple[str, ...]) -> tuple[str, ...]:
    preferred = ("Heavy Armor", "Light Armor", "Medium Armor", "Plate", "Shields")
    ignored = {"Heavy", "Light", "Medium", "Armor"}
    ordered = [value for value in preferred if value in values]
    ordered.extend(value for value in values if value not in preferred and value not in ignored)
    return tuple(ordered)


def _is_cleric_sheet(text: str) -> bool:
    class_level = _extract_labeled_line(text, "class & level") or ""
    return bool(re.search(r"\bcleric\b", class_level, flags=re.I))


def _split_proficiency_values(value: str) -> tuple[str, ...]:
    parts = _split_inventory_line(re.sub(r"\s+", " ", value))
    return tuple(dict.fromkeys(part.strip() for part in parts if part.strip()))


def _extract_damage_resistances(text: str) -> tuple[DamageType, ...]:
    values = []
    for match in re.finditer(r"\bresistances?\s*-\s*(.+)$", text, flags=re.I | re.M):
        values.extend(_split_list(match.group(1).replace("*", "")))
    if re.search(r"\bresistance\s+against\s+poison\s+damage\b", text, flags=re.I):
        values.append("poison")
    resistances = []
    for value in values:
        normalized = value.strip().lower()
        try:
            resistances.append(DamageType(normalized))
        except ValueError:
            continue
    return tuple(dict.fromkeys(resistances))


def _extract_features(text: str) -> tuple[str, ...]:
    class_features = _extract_class_features(text)
    if class_features:
        return _expand_channel_divinity_features(class_features, text)
    known_features = _known_features_in_text(text)
    if known_features:
        return _expand_channel_divinity_features(known_features, text)
    features = [
        match.strip()
        for match in re.findall(r"^\*\s*([^-\n|]+?)(?:\s*-\s*[A-Z][A-Za-z]*\s+\d+)?$", text, re.M)
    ]
    return _expand_channel_divinity_features(
        tuple(dict.fromkeys(feature for feature in features if feature)),
        text,
    )


def _expand_channel_divinity_features(
    features: tuple[str, ...],
    text: str,
) -> tuple[str, ...]:
    """Keep named Channel Divinity options available as imported abilities."""
    expanded = list(features)
    has_channel_divinity = any(
        feature.casefold() == "channel divinity"
        or feature.casefold().startswith("channel divinity:")
        for feature in expanded
    ) or bool(re.search(r"\bchannel\s+divinity\b", text, flags=re.I))
    if not has_channel_divinity:
        return tuple(dict.fromkeys(expanded))
    if not any(feature.casefold() == "channel divinity: turn undead" for feature in expanded):
        expanded.append("Channel Divinity: Turn Undead")
    if _is_life_domain_sheet(text) and not any(
        feature.casefold() == "channel divinity: preserve life" for feature in expanded
    ):
        expanded.append("Channel Divinity: Preserve Life")
    return tuple(dict.fromkeys(expanded))


def _is_life_domain_sheet(text: str) -> bool:
    return bool(
        re.search(
            r"\blife\s+domain\b|\bdivine\s+domain\s*:\s*life\b|\bblessed\s+healer\b",
            text,
            re.I,
        )
    )


def _extract_class_features(text: str) -> tuple[str, ...]:
    class_level = _extract_labeled_line(text, "class & level") or ""
    class_match = re.search(r"\b([A-Za-z]+)\b", class_level)
    class_name = class_match.group(1) if class_match else ""
    headings = [f"{class_name} Features"] if class_name else []
    headings.append("Class Features")
    features: list[str] = []
    for heading in headings:
        block = _extract_equals_heading_block(text, heading)
        if not block:
            continue
        features.extend(_split_feature_block(block))
        break
    return tuple(dict.fromkeys(feature for feature in features if feature))


def _known_features_in_text(text: str) -> tuple[str, ...]:
    features: list[str] = []
    if _is_cleric_sheet(text):
        for pattern, display in (
            (r"\bspellcasting\b", "Spellcasting"),
            (r"\bdivine\s+domain\b|\blife\s+domain\b", "Divine Domain: Life"),
            (r"\bdisciple\s+of\s+life\b|\bdisciple\b", "Disciple of Life"),
            (r"\bchannel\s+divinity\b|\bdivinity:\s*undead\b", "Channel Divinity"),
            (r"\bturn\s+undead\b|\bdivinity:\s*undead\b", "Channel Divinity: Turn Undead"),
            (r"\bpreserve\s+life\b|\bpreserve\b", "Channel Divinity: Preserve Life"),
            (r"\bdestroy\s+undead\b|destroyed\s+if\s+it\s+is\s+of\s+cr", "Destroy Undead"),
            (r"\bblessed\s+healer\b", "Blessed Healer"),
        ):
            if re.search(pattern, text, flags=re.I):
                features.append(display)
    if re.search(r"\bdwarven\s+resilience\b", text, flags=re.I):
        features.append("Dwarven Resilience")
    if re.search(r"\bstonecunning\b", text, flags=re.I):
        features.append("Stonecunning")
    return tuple(dict.fromkeys(features))


def _split_feature_block(value: str) -> list[str]:
    features = []
    for line in _clean_lines(value):
        cleaned = re.sub(r"^\*\s*", "", line).strip(" .:-")
        cleaned = re.sub(r"\s*-\s*[A-Z][A-Za-z]*\s+\d+$", "", cleaned).strip()
        if cleaned:
            features.append(cleaned)
    return features


def _extract_spells(text: str) -> tuple[str, ...]:
    """Extract prepared SRD spells from numbered spellcasting sections."""
    headings = list(
        re.finditer(
            r"^===\s*(?P<level>CANTRIPS|\d+(?:ST|ND|RD|TH)\s+LEVEL)\s*===\s*$",
            text,
            flags=re.I | re.M,
        )
    )
    if not headings:
        return ()
    imported: list[str] = []
    for index, heading in enumerate(headings):
        level_text = heading.group("level").casefold()
        if level_text == "cantrips":
            continue
        level_match = re.match(r"(\d+)", level_text)
        if level_match is None:
            continue
        spell_level = int(level_match.group(1))
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = re.sub(r"\s+", " ", text[heading.end() : end]).strip()
        for spell_name, catalog_level in _srd_spell_catalog():
            if catalog_level == spell_level and _spell_name_in_text(spell_name, section):
                imported.append(spell_name)
    return tuple(dict.fromkeys(imported))


@lru_cache(maxsize=1)
def _srd_spell_catalog() -> tuple[tuple[str, int], ...]:
    """Return SRD spell names and levels used to recognize PDF spell rows."""
    path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "srd_catalog"
        / "srd_spells_level_0_5.json"
    )
    try:
        raw_catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    entries = raw_catalog.get("entries", []) if isinstance(raw_catalog, dict) else []
    return tuple(
        (str(entry["name"]), int(entry["spell_level"]))
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("name")
        and entry.get("spell_level") is not None
        and int(entry["spell_level"]) > 0
    )


def _spell_name_in_text(spell_name: str, text: str) -> bool:
    pattern = re.escape(spell_name).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![A-Za-z]){pattern}(?![A-Za-z])", text, flags=re.I) is not None


def _known_spell_names_in_text(text: str) -> tuple[str, ...]:
    spells = []
    for spell in _KNOWN_IMPORT_SPELLS:
        if re.search(rf"\b{re.escape(spell)}\b", text, flags=re.I):
            spells.append(spell)
    return tuple(spells)


def _extract_labeled_line(text: str, label: str) -> str | None:
    match = re.search(
        rf"^{re.escape(label)}\s*:\s*(.+)$",
        text,
        flags=re.I | re.M,
    )
    if match and match.group(1).strip():
        return match.group(1).strip()
    lines = _clean_lines(text)
    for index, line in enumerate(lines[:-1]):
        if line.lower() == label.lower():
            return lines[index + 1]
    return None


def _ability_display_name(value: str) -> str | None:
    normalized = value.strip().lower()
    return _ABILITY_DISPLAY_NAMES.get(normalized) or _ABILITY_SHORT_NAMES.get(normalized[:3])


def _clean_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _protect_comma_item_names(value: str) -> str:
    protected = value
    for name in _COMMA_ITEM_NAMES:
        protected = re.sub(
            re.escape(name),
            name.replace(",", "<comma>"),
            protected,
            flags=re.I,
        )
    return protected


def _restore_protected_commas(value: str) -> str:
    return value.replace("<comma>", ",")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80]
