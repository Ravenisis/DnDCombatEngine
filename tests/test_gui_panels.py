from dnd_combat_engine.engine import AttackRequest
from dnd_combat_engine.gui.panels import (
    attack_summary_text,
    campaign_rows,
    character_sheet_rows,
    encounter_rows,
    initiative_rows,
)
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


def test_character_sheet_rows_include_core_state() -> None:
    rows = character_sheet_rows(Character("rogue", "Vale", HitPoints(7, 10, temporary=2)))

    assert ("Name", "Vale") in rows
    assert ("Temporary HP", "2") in rows


def test_campaign_rows_include_workspace_counts() -> None:
    rows = campaign_rows(
        Campaign(
            "starter",
            "Starter",
            character_ids=("vale", "bran"),
            encounter_ids=("roadside_ambush",),
            notes="Opening arc.",
        )
    )

    assert ("Name", "Starter") in rows
    assert ("Characters", "2") in rows
    assert ("Encounters", "1") in rows
    assert ("Notes", "Opening arc.") in rows


def test_attack_summary_text_describes_result() -> None:
    attacker = Character("fighter", "Bran", HitPoints(12, 12))
    target = Character("goblin", "Goblin", HitPoints(7, 7))
    weapon = Weapon(
        "Longsword",
        DamageProfile((DamageComponent("1d8", DamageType.SLASHING),)),
    )
    request = AttackRequest(attacker, target, weapon, target_armor_class=15, attack_bonus=3)
    result = CombatService().resolve_attack(request, rng=SequenceRng([12, 4]))  # type: ignore[arg-type]

    assert "Bran -> Goblin [HIT]" in attack_summary_text(result)


def test_encounter_and_initiative_panel_rows() -> None:
    character = Character("rogue", "Vale", HitPoints(10, 10))
    encounter = Encounter(
        "ambush",
        "Ambush",
        participants=(
            EncounterParticipant("goblin", "Goblin", ParticipantKind.MONSTER, "goblin", 2),
        ),
    )
    tracker = InitiativeService().roll_initiative(
        (character,),
        rng=SequenceRng([10]),  # type: ignore[arg-type]
    )

    assert ("Participants", "2") in encounter_rows(encounter)
    assert ("Active", "Vale") in initiative_rows(tracker)
