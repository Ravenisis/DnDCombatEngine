from fractions import Fraction

from dnd_combat_engine.controllers import EncounterController
from dnd_combat_engine.models import (
    AbilityScores,
    Character,
    Encounter,
    EncounterStatus,
    HitPoints,
    Monster,
    ParticipantKind,
)
from dnd_combat_engine.persistence import JsonFileStore
from dnd_combat_engine.services import EncounterService, InitiativeService, PersistenceService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def make_controller(tmp_path) -> EncounterController:
    return EncounterController(
        encounter_service=EncounterService(),
        initiative_service=InitiativeService(),
        persistence_service=PersistenceService(JsonFileStore(tmp_path)),
    )


def test_encounter_controller_adds_participants_and_persists(tmp_path) -> None:
    controller = make_controller(tmp_path)
    encounter = Encounter("ambush", "Ambush")
    character = Character(
        "rogue",
        "Vale",
        HitPoints(10, 10),
        abilities=AbilityScores(dexterity=16),
    )
    monster = Monster(
        monster_id="goblin",
        name="Goblin",
        armor_class=15,
        hit_points=HitPoints(7, 7),
        abilities=AbilityScores(dexterity=14),
        challenge_rating=Fraction(1, 4),
    )

    encounter = controller.add_character(encounter, character)
    encounter = controller.add_monster(encounter, monster, quantity=2)
    controller.save(encounter)
    restored = controller.load("ambush")

    assert [participant.kind for participant in restored.participants] == [
        ParticipantKind.CHARACTER,
        ParticipantKind.MONSTER,
    ]
    assert restored.participants[1].quantity == 2


def test_encounter_controller_starts_and_rolls_initiative(tmp_path) -> None:
    controller = make_controller(tmp_path)
    character = Character(
        "rogue",
        "Vale",
        HitPoints(10, 10),
        abilities=AbilityScores(dexterity=16),
    )
    encounter = controller.add_character(Encounter("ambush", "Ambush"), character)

    active, tracker = controller.start_and_roll_initiative(
        encounter,
        (character,),
        rng=SequenceRng([12]),  # type: ignore[arg-type]
    )

    assert active.status is EncounterStatus.ACTIVE
    assert tracker.current.combatant is character
    assert tracker.current.total == 15

