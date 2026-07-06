from fractions import Fraction

from dnd_combat_engine.controllers import CombatController
from dnd_combat_engine.engine import AttackRequest
from dnd_combat_engine.gui.panels import (
    attack_summary_text,
    campaign_reference_rows,
    campaign_rows,
    character_sheet_rows,
    encounter_participant_rows,
    encounter_rows,
    initiative_rows,
)
from dnd_combat_engine.gui.widgets import _quick_attack_message
from dnd_combat_engine.models import (
    Campaign,
    Character,
    DamageComponent,
    DamageProfile,
    DamageType,
    Encounter,
    EncounterParticipant,
    HitPoints,
    Monster,
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
    campaign = Campaign(
        "starter",
        "Starter",
        character_ids=("vale", "bran"),
        encounter_ids=("roadside_ambush",),
        notes="Opening arc.",
    )
    rows = campaign_rows(campaign)

    assert ("Name", "Starter") in rows
    assert ("Characters", "2") in rows
    assert ("Encounters", "1") in rows
    assert ("Notes", "Opening arc.") in rows
    assert ("Character", "vale") in campaign_reference_rows(campaign)
    assert ("Encounter", "roadside_ambush") in campaign_reference_rows(campaign)


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


def test_quick_attack_uses_first_campaign_character() -> None:
    ravenisis = Character(
        "ravenisis",
        "Ravenisis",
        HitPoints(20, 20),
        weapons=(
            Weapon(
                "Handaxe",
                DamageProfile((DamageComponent("1d6", DamageType.SLASHING),)),
            ),
        ),
    )
    goblin = Monster(
        "goblin",
        "Goblin",
        armor_class=10,
        hit_points=HitPoints(7, 7),
        abilities=ravenisis.abilities,
        challenge_rating=Fraction(1, 4),
    )
    app = _quick_attack_app(ravenisis, goblin)

    message = _quick_attack_message(app, campaign_id="starter_campaign")

    assert "Ravenisis -> Goblin" in message


def test_quick_attack_reports_missing_weapon() -> None:
    ravenisis = Character("ravenisis", "Ravenisis", HitPoints(20, 20))
    goblin = Monster(
        "goblin",
        "Goblin",
        armor_class=10,
        hit_points=HitPoints(7, 7),
        abilities=ravenisis.abilities,
        challenge_rating=Fraction(1, 4),
    )
    app = _quick_attack_app(ravenisis, goblin)

    assert _quick_attack_message(app, campaign_id="starter_campaign") == (
        "Ravenisis has no weapon configured for Quick Attack."
    )


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
    assert encounter_participant_rows(encounter) == [("goblin", "Goblin", "monster", "2")]
    assert ("Active", "Vale") in initiative_rows(tracker)


def _quick_attack_app(character: Character, monster: Monster):
    class Characters:
        def load(self, character_id: str) -> Character:
            assert character_id == character.character_id
            return character

    class Campaigns:
        def load(self, campaign_id: str) -> Campaign:
            assert campaign_id == "starter_campaign"
            return Campaign(campaign_id, "Starter", character_ids=(character.character_id,))

    class Compendium:
        def load_monster(self, monster_id: str) -> Monster:
            assert monster_id == monster.monster_id
            return monster

    class SequenceCombat(CombatController):
        def attack_with_weapon(self, *args, **kwargs):  # noqa: ANN002, ANN003
            kwargs["rng"] = SequenceRng([12, 4])  # type: ignore[assignment]
            return super().attack_with_weapon(*args, **kwargs)

    return type(
        "QuickAttackApp",
        (),
        {
            "characters": Characters(),
            "campaigns": Campaigns(),
            "compendium": Compendium(),
            "combat": SequenceCombat(CombatService()),
        },
    )()
