from fractions import Fraction

from dnd_combat_engine.models import (
    AbilityScores,
    Campaign,
    Character,
    Encounter,
    EncounterParticipant,
    HitPoints,
    HostedCampaignSession,
    HostedPlayer,
    Monster,
    ParticipantKind,
    PlayerRole,
    Spell,
    SpellSchool,
)
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.persistence.migrations import migrate_character
from dnd_combat_engine.services import PersistenceService


def test_persistence_service_saves_and_loads_character(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    character = Character(
        character_id="fighter-1",
        name="Bran",
        hit_points=HitPoints(current=12, maximum=12),
    )

    service.save_character(character)

    assert service.list_character_ids() == ["fighter-1"]
    assert service.load_character("fighter-1") == character
    assert service.store.load("characters", "fighter-1")["schema_version"] == 1


def test_persistence_service_saves_and_loads_campaign(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    campaign = Campaign(
        campaign_id="starter",
        name="Starter",
        character_ids=("vale",),
        encounter_ids=("roadside_ambush",),
    )

    service.save_campaign(campaign)

    assert service.list_campaign_ids() == ["starter"]
    assert service.load_campaign("starter") == campaign
    assert service.store.load("campaigns", "starter")["schema_version"] == 1


def test_persistence_service_saves_and_loads_hosted_session(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    session = HostedCampaignSession(
        session_id="starter-ABC123",
        campaign_id="starter",
        join_code="ABC123",
        host_player_id="host",
        players=(HostedPlayer("host", "DM", PlayerRole.HOST),),
    )

    service.save_hosted_session(session)

    assert service.list_hosted_session_ids() == ["starter-ABC123"]
    assert service.load_hosted_session("starter-ABC123") == session
    assert service.store.load("hosted_sessions", "starter-ABC123")["schema_version"] == 1


def test_persistence_service_saves_and_loads_spell(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    spell = Spell(
        spell_id="shield",
        name="Shield",
        level=1,
        school=SpellSchool.ABJURATION,
        casting_time="1 reaction",
        range_text="Self",
        duration="1 round",
    )

    service.save_spell(spell)

    assert service.list_spell_ids() == ["shield"]
    assert service.load_spell("shield") == spell
    assert service.store.load("spells", "shield")["schema_version"] == 1


def test_persistence_materializes_class_catalog_spells(tmp_path) -> None:
    store = JsonFileStore(tmp_path)
    store.save(
        "class_spell_lists",
        "cleric",
        {
            "class_id": "cleric",
            "spells": [
                {
                    "spell_id": "detect_magic",
                    "name": "Detect Magic",
                    "level": 1,
                    "school": "divination",
                    "ritual": True,
                },
                {
                    "spell_id": "spirit_guardians",
                    "name": "Spirit Guardians",
                    "level": 3,
                    "school": "conjuration",
                },
            ],
        },
    )
    service = PersistenceService(store)

    assert service.class_spell_ids("Cleric", 1) == ("detect_magic",)
    spell = service.load_spell("detect_magic")
    assert spell.name == "Detect Magic"
    assert spell.ritual is True
    assert "automation" in spell.description


def test_persistence_service_saves_and_loads_monster(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    monster = Monster(
        monster_id="goblin",
        name="Goblin",
        armor_class=15,
        hit_points=HitPoints(current=7, maximum=7),
        abilities=AbilityScores(dexterity=14),
        challenge_rating=Fraction(1, 4),
    )

    service.save_monster(monster)

    assert service.list_monster_ids() == ["goblin"]
    assert service.load_monster("goblin") == monster
    assert service.store.load("monsters", "goblin")["schema_version"] == 1


def test_persistence_service_saves_and_loads_encounter(tmp_path) -> None:
    service = PersistenceService(JsonFileStore(tmp_path))
    encounter = Encounter(
        encounter_id="ambush-1",
        name="Roadside Ambush",
        participants=(
            EncounterParticipant(
                participant_id="goblin",
                name="Goblin",
                kind=ParticipantKind.MONSTER,
                source_id="goblin",
                quantity=3,
            ),
        ),
    )

    service.save_encounter(encounter)

    assert service.list_encounter_ids() == ["ambush-1"]
    assert service.load_encounter("ambush-1") == encounter
    assert service.store.load("encounters", "ambush-1")["schema_version"] == 1


def test_persistence_service_migrates_legacy_character_without_schema_version(
    tmp_path,
) -> None:
    store = JsonFileStore(tmp_path)
    store.save(
        "characters",
        "legacy",
        {
            "character_id": "legacy",
            "name": "Legacy",
            "hit_points": {"current": 8, "maximum": 8, "temporary": 0},
            "abilities": AbilityScores().to_dict(),
        },
    )

    character = PersistenceService(store).load_character("legacy")

    assert character.name == "Legacy"
    assert migrate_character(store.load("characters", "legacy"))["schema_version"] == 1


def test_migrations_reject_future_schema_versions() -> None:
    try:
        migrate_character({"schema_version": 999})
    except ValueError as exc:
        assert "newer than supported" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_store_lists_missing_collection_as_empty(tmp_path) -> None:
    store = JsonFileStore(tmp_path)

    assert store.list_ids("characters") == []


def test_store_rejects_missing_collection_or_id(tmp_path) -> None:
    store = JsonFileStore(tmp_path)

    for collection, entity_id in [("", "x"), ("characters", "")]:
        try:
            store.save(collection, entity_id, {})
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def test_store_rejects_non_object_json(tmp_path) -> None:
    path = tmp_path / "characters"
    path.mkdir()
    (path / "bad.json").write_text("[]", encoding="utf-8")
    store = JsonFileStore(tmp_path)

    try:
        store.load("characters", "bad")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
