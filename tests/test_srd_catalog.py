from pathlib import Path

from dnd_combat_engine.models import SrdCatalog
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import PersistenceService, SrdCatalogService

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"


def test_srd_spell_catalog_covers_spell_levels_available_by_character_level_ten() -> None:
    catalog = SrdCatalog.from_dict(
        JsonFileStore(DATA_ROOT).load("srd_catalog", "srd_spells_level_0_5")
    )
    entries = {entry.name: entry for entry in catalog.entries}

    assert len(catalog.entries) >= 250
    assert catalog.max_character_level == 10
    assert {entry.spell_level for entry in catalog.entries} == {0, 1, 2, 3, 4, 5}
    assert all(entry.entry_type == "spell" for entry in catalog.entries)
    assert all(
        entry.spell_level is not None and entry.spell_level <= 5
        for entry in catalog.entries
    )
    assert entries["Fireball"].spell_level == 3
    assert entries["Cure Wounds"].classes == ("Bard", "Cleric", "Druid", "Paladin", "Ranger")
    assert entries["Teleportation Circle"].spell_level == 5
    assert "Wish" not in entries


def test_srd_class_catalog_covers_base_and_srd_subclass_features_through_level_ten() -> None:
    catalog = SrdCatalog.from_dict(
        JsonFileStore(DATA_ROOT).load("srd_catalog", "srd_class_features_level_1_10")
    )
    entries = {(entry.owner, entry.name): entry for entry in catalog.entries}

    assert len(catalog.entries) >= 190
    assert all(entry.level is None or entry.level <= 10 for entry in catalog.entries)
    assert entries[("Barbarian", "Rage")].level == 1
    assert entries[("Cleric", "Divine Intervention")].level == 10
    assert entries[("Path of the Berserker", "Retaliation")].level == 10
    assert entries[("Evoker", "Empowered Evocation")].level == 10
    assert entries[("Fiend Patron", "Fiendish Resilience")].level == 10
    assert ("Wizard", "Spell Mastery") not in entries


def test_srd_species_catalog_covers_species_traits_and_lineage_options() -> None:
    catalog = SrdCatalog.from_dict(
        JsonFileStore(DATA_ROOT).load("srd_catalog", "srd_species_traits_level_1_10")
    )
    entries = {(entry.owner, entry.name): entry for entry in catalog.entries}
    owners = {entry.owner for entry in catalog.entries}

    assert owners == {
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
    assert entries[("Dragonborn", "Breath Weapon")].entry_type == "species_trait"
    assert entries[("Dwarf", "Dwarven Resilience")].entry_type == "species_trait"
    assert entries[("Goliath", "Stone's Endurance")].entry_type == "species_trait_option"
    assert entries[("Elf", "Drow Lineage")].entry_type == "species_trait_option"
    assert entries[("Tiefling", "Infernal Legacy")].entry_type == "species_trait_option"


def test_srd_catalog_service_filters_by_owner_and_level() -> None:
    service = SrdCatalogService(PersistenceService(JsonFileStore(DATA_ROOT)))

    cleric_features = service.entries_for_owner("srd_class_features_level_1_10", "Cleric")
    low_level_features = service.entries_up_to_level("srd_class_features_level_1_10", 2)

    assert {entry.name for entry in cleric_features} >= {"Spellcasting", "Channel Divinity"}
    assert all(entry.level is None or entry.level <= 2 for entry in low_level_features)
