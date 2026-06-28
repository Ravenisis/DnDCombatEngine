from fractions import Fraction

import pytest

from dnd_combat_engine.models import (
    AbilityScores,
    Character,
    Encounter,
    EncounterParticipant,
    EncounterStatus,
    HitPoints,
    Monster,
    ParticipantKind,
)


def make_character() -> Character:
    return Character(
        character_id="rogue-1",
        name="Vale",
        hit_points=HitPoints(current=9, maximum=9),
        abilities=AbilityScores(dexterity=16),
    )


def make_monster() -> Monster:
    return Monster(
        monster_id="goblin",
        name="Goblin",
        armor_class=15,
        hit_points=HitPoints(current=7, maximum=7),
        abilities=AbilityScores(dexterity=14),
        challenge_rating=Fraction(1, 4),
    )


def test_encounter_participant_builds_from_character_and_monster() -> None:
    character = EncounterParticipant.from_character(make_character())
    monster = EncounterParticipant.from_monster(make_monster(), quantity=3)

    assert character.kind is ParticipantKind.CHARACTER
    assert character.initiative_bonus == 3
    assert monster.kind is ParticipantKind.MONSTER
    assert monster.quantity == 3
    assert monster.initiative_bonus == 2


def test_encounter_round_trips_to_plain_data() -> None:
    encounter = Encounter(
        encounter_id="ambush-1",
        name="Roadside Ambush",
        participants=(EncounterParticipant.from_character(make_character()),),
        status=EncounterStatus.ACTIVE,
        notes="Rainy road",
    )

    restored = Encounter.from_dict(encounter.to_dict())

    assert restored == encounter


def test_encounter_adds_replaces_and_removes_participants() -> None:
    character = EncounterParticipant.from_character(make_character())
    replacement = EncounterParticipant(
        participant_id=character.participant_id,
        name="Vale Shadowstep",
        kind=ParticipantKind.CHARACTER,
        source_id=character.source_id,
    )
    encounter = Encounter("ambush-1", "Roadside Ambush").with_participant(character)

    replaced = encounter.with_participant(replacement)
    removed = replaced.without_participant(character.participant_id)

    assert replaced.participants == (replacement,)
    assert removed.participants == ()


def test_encounter_validates_values() -> None:
    participant_kwargs = {
        "participant_id": "x",
        "name": "X",
        "kind": ParticipantKind.CHARACTER,
        "source_id": "x",
    }

    with pytest.raises(ValueError):
        Encounter("", "Name")
    with pytest.raises(ValueError):
        Encounter("id", "")
    with pytest.raises(ValueError):
        Encounter("id", "Name", round_number=0)
    with pytest.raises(ValueError):
        EncounterParticipant(**{**participant_kwargs, "participant_id": ""})
    with pytest.raises(ValueError):
        EncounterParticipant(**{**participant_kwargs, "name": ""})
    with pytest.raises(ValueError):
        EncounterParticipant(**{**participant_kwargs, "source_id": ""})
    with pytest.raises(ValueError):
        EncounterParticipant(**{**participant_kwargs, "quantity": 0})

