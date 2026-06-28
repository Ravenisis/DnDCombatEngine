import pytest

from dnd_combat_engine.models import (
    Encounter,
    EncounterParticipant,
    EncounterStatus,
    ParticipantKind,
)
from dnd_combat_engine.services import EncounterService


def make_participant(
    participant_id: str = "goblin",
    quantity: int = 1,
    kind: ParticipantKind = ParticipantKind.MONSTER,
) -> EncounterParticipant:
    return EncounterParticipant(
        participant_id=participant_id,
        name=participant_id.title(),
        kind=kind,
        source_id=participant_id,
        quantity=quantity,
    )


def test_encounter_service_manages_lifecycle() -> None:
    service = EncounterService()
    encounter = Encounter("ambush-1", "Roadside Ambush")

    with_participant = service.add_participant(encounter, make_participant(quantity=2))
    active = service.start(with_participant)
    next_round = service.advance_round(active)
    completed = service.complete(next_round)

    assert active.status is EncounterStatus.ACTIVE
    assert active.round_number == 1
    assert next_round.round_number == 2
    assert completed.status is EncounterStatus.COMPLETED
    assert service.total_monsters(completed) == 2


def test_encounter_service_removes_participants() -> None:
    service = EncounterService()
    encounter = service.add_participant(
        Encounter("ambush-1", "Roadside Ambush"),
        make_participant(),
    )

    updated = service.remove_participant(encounter, "goblin")

    assert updated.participants == ()


def test_encounter_service_rejects_invalid_transitions() -> None:
    service = EncounterService()
    completed = Encounter("ambush-1", "Roadside Ambush", status=EncounterStatus.COMPLETED)
    active = Encounter(
        "ambush-1",
        "Roadside Ambush",
        participants=(make_participant(),),
        status=EncounterStatus.ACTIVE,
    )

    with pytest.raises(ValueError):
        service.start(Encounter("empty", "Empty"))
    with pytest.raises(ValueError):
        service.advance_round(Encounter("draft", "Draft"))
    with pytest.raises(ValueError):
        service.add_participant(completed, make_participant())
    with pytest.raises(ValueError):
        service.remove_participant(completed, "goblin")

    assert service.complete(active).round_number == 1
