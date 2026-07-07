from dnd_combat_engine.controllers import (
    AttackSummary,
    CampaignSummary,
    CharacterSummary,
    EncounterSummary,
    InitiativeSummary,
)
from dnd_combat_engine.engine import AttackRequest
from dnd_combat_engine.models import (
    Campaign,
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    Encounter,
    EncounterParticipant,
    HitPoints,
    ParticipantKind,
    Weapon,
)
from dnd_combat_engine.services import CombatService, InitiativeService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def test_character_summary_from_character() -> None:
    character = Character("rogue", "Vale", HitPoints(7, 10, temporary=2))

    summary = CharacterSummary.from_character(character)

    assert summary.name == "Vale"
    assert summary.current_hp == 7
    assert summary.temporary_hp == 2


def test_campaign_summary_from_campaign() -> None:
    campaign = Campaign(
        "starter",
        "Starter",
        character_ids=("vale",),
        encounter_ids=("roadside_ambush",),
    )

    summary = CampaignSummary.from_campaign(campaign)

    assert summary.name == "Starter"
    assert summary.status == "planned"
    assert summary.character_count == 1
    assert summary.encounter_count == 1


def test_attack_summary_from_result() -> None:
    attacker = Character("fighter", "Bran", HitPoints(12, 12))
    target = Character("goblin", "Goblin", HitPoints(7, 7))
    weapon = Weapon(
        "Longsword",
        DamageProfile((DamageComponent("1d8", DamageType.SLASHING),)),
    )
    request = AttackRequest(attacker, target, weapon, target_armor_class=15, attack_bonus=3)
    result = CombatService().resolve_attack(request, rng=SequenceRng([12, 4]))  # type: ignore[arg-type]

    summary = AttackSummary.from_result(result)

    assert summary.attacker == "Bran"
    assert summary.hit is True
    assert summary.critical_miss is False
    assert summary.damage_applied == 4


def test_encounter_and_initiative_summaries() -> None:
    character = Character("rogue", "Vale", HitPoints(10, 10))
    encounter = Encounter(
        "ambush",
        "Ambush",
        participants=(
            EncounterParticipant("goblin", "Goblin", ParticipantKind.MONSTER, "goblin", 3),
        ),
    )
    tracker = InitiativeService().roll_initiative(
        (character,),
        rng=SequenceRng([10]),  # type: ignore[arg-type]
    )

    encounter_summary = EncounterSummary.from_encounter(encounter)
    initiative_summary = InitiativeSummary.from_tracker(tracker)

    assert encounter_summary.participant_count == 3
    assert initiative_summary.active_combatant == "Vale"
    assert initiative_summary.order == ("Vale",)
