from dnd_combat_engine.models import Spell
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import PersistenceService
from dnd_combat_engine.srd_spells import (
    MAX_SUPPORTED_SPELL_LEVEL,
    get_srd_spell_data,
    list_srd_spell_ids,
    srd_spell_level_counts,
)


def test_srd_spell_compendium_covers_levels_zero_through_five() -> None:
    spell_ids = list_srd_spell_ids()
    counts = srd_spell_level_counts()

    assert MAX_SUPPORTED_SPELL_LEVEL == 5
    assert counts.keys() == {0, 1, 2, 3, 4, 5}
    assert sum(counts.values()) == len(spell_ids)
    assert len(spell_ids) >= 200
    assert {"fireball", "raise_dead", "wall_of_force", "revivify"}.issubset(spell_ids)


def test_persistence_lists_and_loads_builtin_srd_spells(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))

    spell_ids = service.list_spell_ids()
    bless = service.load_spell("bless")
    fireball = service.load_spell("fireball")
    raise_dead = service.load_spell("raise_dead")

    assert "bless" in spell_ids
    assert bless.level == 1
    assert bless.concentration is True
    assert bless.effects[0].effect_kind.value == "buff"
    assert bless.effects[0].resource_cost == "spell_slot_1"
    assert fireball.level == 3
    assert fireball.damage is not None
    assert fireball.effects[0].dice == "8d6"
    assert raise_dead.level == 5
    assert raise_dead.effects[0].effect_kind.value == "healing"


def test_saved_spell_overrides_builtin_srd_spell(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    builtin = service.load_spell("bless")
    custom = Spell.from_dict({**builtin.to_dict(), "name": "Campaign Bless"})

    service.save_spell(custom)

    assert service.load_spell("bless").name == "Campaign Bless"


def test_srd_spell_entries_include_rule_source_metadata() -> None:
    data = get_srd_spell_data("detect_magic")

    assert data is not None
    assert data["ritual"] is True
    assert data["rule_source"]["version"] == "5.2.1"
    assert data["effects"][0]["rule_source"]["license_name"].startswith("Creative Commons")
