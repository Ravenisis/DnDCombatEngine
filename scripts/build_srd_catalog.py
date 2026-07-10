"""Build compact SRD support catalogs from SRD markdown files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SOURCE = {
    "name": "System Reference Document",
    "version": "5.2.1",
    "license_name": "Creative Commons Attribution 4.0 International License",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "attribution": "SRD 5.2.1 Copyright 2024 Wizards of the Coast LLC.",
}
CLASS_NAMES = {
    "Barbarian",
    "Bard",
    "Cleric",
    "Druid",
    "Fighter",
    "Monk",
    "Paladin",
    "Ranger",
    "Rogue",
    "Sorcerer",
    "Warlock",
    "Wizard",
}
SPECIES_NAMES = {
    "Dragonborn",
    "Dwarf",
    "Elf",
    "Gnome",
    "Goliath",
    "Halfling",
    "Human",
    "Orc",
    "Tiefling",
}
LINEAGE_OPTIONS = {
    "Elf": ("Drow Lineage", "High Elf Lineage", "Wood Elf Lineage"),
    "Gnome": ("Forest Gnome Lineage", "Rock Gnome Lineage"),
    "Goliath": (
        "Cloud's Jaunt",
        "Fire's Burn",
        "Frost's Chill",
        "Hill's Tumble",
        "Stone's Endurance",
        "Storm's Thunder",
    ),
    "Tiefling": ("Abyssal Legacy", "Chthonic Legacy", "Infernal Legacy"),
}


def main() -> int:
    """Generate SRD catalog JSON files."""
    parser = argparse.ArgumentParser()
    parser.add_argument("srd_root", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    srd_root = args.srd_root
    repo_root = args.repo_root
    catalogs = {
        "srd_spells_level_0_5": spell_catalog(srd_root / "spells.md"),
        "srd_class_features_level_1_10": class_feature_catalog(srd_root / "classes.md"),
        "srd_species_traits_level_1_10": species_trait_catalog(
            srd_root / "character-origins.md"
        ),
    }
    for root in (repo_root / "data", repo_root / "src" / "dnd_combat_engine" / "data"):
        directory = root / "srd_catalog"
        directory.mkdir(parents=True, exist_ok=True)
        for catalog_id, payload in catalogs.items():
            (directory / f"{catalog_id}.json").write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    return 0


def spell_catalog(path: Path) -> dict[str, Any]:
    """Build the compact spell catalog."""
    entries = []
    pending_name = ""
    pending_line = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        heading = re.fullmatch(r"#### (.+)", line)
        if heading:
            pending_name = heading.group(1).strip()
            pending_line = line_number
            continue
        level_spell = re.fullmatch(r"_Level (\d+) ([A-Za-z]+) \(([^)]+)\)_", line)
        cantrip = re.fullmatch(r"_([A-Za-z]+) Cantrip \(([^)]+)\)_", line)
        if not pending_name or (level_spell is None and cantrip is None):
            continue
        level = 0 if cantrip is not None else int(level_spell.group(1))
        if level > 5:
            pending_name = ""
            continue
        school = cantrip.group(1) if cantrip is not None else level_spell.group(2)
        classes_text = cantrip.group(2) if cantrip is not None else level_spell.group(3)
        entries.append(
            {
                "entry_id": slug(pending_name),
                "name": pending_name,
                "entry_type": "spell",
                "owner": "",
                "level": None,
                "spell_level": level,
                "school": school.lower(),
                "classes": split_classes(classes_text),
                "source_reference": f"spells.md:L{pending_line}",
                "automation_status": "cataloged",
            }
        )
        pending_name = ""
    return catalog(
        "srd_spells_level_0_5",
        "SRD spells available by character level 10",
        entries,
        "Spells of level 0 through 5 are cataloged because full casters reach "
        "5th-level spells by character level 9.",
    )


def class_feature_catalog(path: Path) -> dict[str, Any]:
    """Build the compact class and subclass feature catalog."""
    entries = []
    current_owner = ""
    in_class_or_subclass = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        class_heading = re.fullmatch(r"## (.+)", line)
        if class_heading and class_heading.group(1) in CLASS_NAMES:
            current_owner = class_heading.group(1)
            in_class_or_subclass = False
            continue
        subsection = re.fullmatch(r"### (.+)", line)
        if subsection:
            title = subsection.group(1)
            if title.endswith("Class Features"):
                in_class_or_subclass = True
                current_owner = title.removesuffix(" Class Features")
            elif "Subclass:" in title:
                in_class_or_subclass = True
                current_owner = title.split("Subclass:", 1)[1].strip()
            elif title.endswith("Options"):
                in_class_or_subclass = True
                current_owner = title
            else:
                in_class_or_subclass = False
            continue
        level_feature = re.fullmatch(r"#### Level (\d+): (.+)", line)
        if in_class_or_subclass and level_feature:
            level = int(level_feature.group(1))
            if level <= 10:
                name = level_feature.group(2).strip()
                entries.append(
                    {
                        "entry_id": slug(f"{current_owner}-{level}-{name}"),
                        "name": name,
                        "entry_type": (
                            "subclass_feature"
                            if current_owner not in CLASS_NAMES
                            else "class_feature"
                        ),
                        "owner": current_owner,
                        "level": level,
                        "spell_level": None,
                        "school": "",
                        "classes": [],
                        "source_reference": f"classes.md:L{line_number}",
                        "automation_status": "cataloged",
                    }
                )
            continue
        option = re.fullmatch(r"#### (.+)", line)
        if in_class_or_subclass and option and current_owner.endswith("Options"):
            name = option.group(1).strip()
            entries.append(
                {
                    "entry_id": slug(f"{current_owner}-{name}"),
                    "name": name,
                    "entry_type": "class_option",
                    "owner": current_owner,
                    "level": None,
                    "spell_level": None,
                    "school": "",
                    "classes": [],
                    "source_reference": f"classes.md:L{line_number}",
                    "automation_status": "cataloged",
                }
            )
    return catalog(
        "srd_class_features_level_1_10",
        "SRD class and subclass abilities through level 10",
        entries,
        "Class features, SRD subclass features, metamagic options, and invocation "
        "options are cataloged by name and prerequisite level where the SRD heading "
        "provides one.",
    )


def species_trait_catalog(path: Path) -> dict[str, Any]:
    """Build the compact species trait catalog."""
    entries = []
    current_species = ""
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        species_heading = re.fullmatch(r"#### (.+)", line)
        if species_heading and species_heading.group(1) in SPECIES_NAMES:
            current_species = species_heading.group(1)
            continue
        if not current_species:
            continue
        trait = re.match(r"_([^_.]+)\._", line)
        if trait:
            name = trait.group(1).strip()
            entries.append(
                species_entry(current_species, name, "species_trait", line_number, level=1)
            )
            continue
        option = re.match(r"\*\*([^*.]+)\.\*\*", line)
        if option and current_species in LINEAGE_OPTIONS:
            name = option.group(1).strip()
            entries.append(
                species_entry(current_species, name, "species_trait_option", line_number, level=1)
            )
    for species, options in LINEAGE_OPTIONS.items():
        existing = {entry["name"] for entry in entries if entry["owner"] == species}
        for name in options:
            if name not in existing:
                entries.append(species_entry(species, name, "species_trait_option", 0, level=1))
    return catalog(
        "srd_species_traits_level_1_10",
        "SRD species traits through level 10",
        entries,
        "SRD 5.2.1 species traits are cataloged as racial/species abilities for "
        "character-builder compatibility.",
    )


def species_entry(
    species: str,
    name: str,
    entry_type: str,
    line_number: int,
    level: int,
) -> dict[str, Any]:
    """Return a species catalog entry."""
    return {
        "entry_id": slug(f"{species}-{name}"),
        "name": name,
        "entry_type": entry_type,
        "owner": species,
        "level": level,
        "spell_level": None,
        "school": "",
        "classes": [],
        "source_reference": "character-origins.md" + (f":L{line_number}" if line_number else ""),
        "automation_status": "cataloged",
    }


def catalog(
    catalog_id: str,
    title: str,
    entries: list[dict[str, Any]],
    notes: str,
) -> dict[str, Any]:
    """Return a complete SRD catalog payload."""
    return {
        "schema_version": 1,
        "catalog_id": catalog_id,
        "title": title,
        "max_character_level": 10,
        "notes": notes,
        "source": SOURCE,
        "entries": sorted(
            entries,
            key=lambda item: (item["owner"], item["level"] or 0, item["name"]),
        ),
    }


def split_classes(value: str) -> list[str]:
    """Split a spell class list."""
    return [item.strip() for item in value.split(",") if item.strip()]


def slug(value: str) -> str:
    """Return a stable JSON id slug."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
