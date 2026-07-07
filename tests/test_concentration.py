import pytest

from dnd_combat_engine.models import (
    Character,
    ConcentrationOutcome,
    ConcentrationState,
    DurationKind,
    DurationProfile,
    EffectDefinition,
    EffectKind,
    HitPoints,
    TargetKind,
    TargetProfile,
    TargetReference,
    concentration_save_dc,
)
from dnd_combat_engine.models.abilities import AbilityScores
from dnd_combat_engine.services import ConcentrationService


class SequenceRng:
    def __init__(self, values: list[int]) -> None:
        self.values = values

    def randint(self, minimum: int, maximum: int) -> int:
        value = self.values.pop(0)
        assert minimum <= value <= maximum
        return value


def concentration_effect(name: str = "Bless") -> EffectDefinition:
    return EffectDefinition(
        effect_id=name.lower().replace(" ", "-"),
        name=name,
        effect_kind=EffectKind.BUFF,
        target_profile=TargetProfile.MULTIPLE_CREATURES,
        duration=DurationProfile(DurationKind.CONCENTRATION, amount=1, text="up to 1 minute"),
    )


def test_concentration_state_round_trips_to_plain_data() -> None:
    target = TargetReference("ally", "Ally", TargetKind.CHARACTER, "ally")
    state = ConcentrationState(
        caster_id="cleric",
        effect_id="bless",
        effect_name="Bless",
        targets=(target,),
        duration_text="up to 1 minute",
    )

    assert ConcentrationState.from_dict(state.to_dict()) == state


def test_concentration_save_dc_uses_half_damage_or_ten() -> None:
    assert concentration_save_dc(1) == 10
    assert concentration_save_dc(20) == 10
    assert concentration_save_dc(30) == 15
    with pytest.raises(ValueError):
        concentration_save_dc(-1)


def test_concentration_service_starts_and_replaces_effects() -> None:
    caster = Character("cleric", "Mira", HitPoints(12, 12))
    target = TargetReference("ally", "Ally", TargetKind.CHARACTER, "ally")
    service = ConcentrationService()

    started = service.start(caster, concentration_effect(), targets=(target,))
    replaced = service.start(
        caster,
        concentration_effect("Beacon of Hope"),
        targets=(target,),
        current=started.state,
    )

    assert started.outcome == ConcentrationOutcome.STARTED
    assert started.state is not None
    assert started.state.effect_name == "Bless"
    assert started.message() == "cleric starts concentrating on Bless."
    assert replaced.outcome == ConcentrationOutcome.REPLACED
    assert replaced.previous == started.state
    assert replaced.state is not None
    assert replaced.state.effect_name == "Beacon of Hope"


def test_concentration_service_rejects_non_concentration_effect() -> None:
    caster = Character("cleric", "Mira", HitPoints(12, 12))
    effect = EffectDefinition(
        effect_id="cure-wounds",
        name="Cure Wounds",
        effect_kind=EffectKind.HEALING,
        target_profile=TargetProfile.ONE_CREATURE,
    )

    with pytest.raises(ValueError, match="not a concentration effect"):
        ConcentrationService().start(caster, effect)


def test_concentration_check_after_damage_maintains_or_breaks() -> None:
    caster = Character(
        "cleric",
        "Mira",
        HitPoints(12, 12),
        abilities=AbilityScores(constitution=14),
    )
    state = ConcentrationState("cleric", "bless", "Bless")
    service = ConcentrationService()

    maintained = service.check_after_damage(
        caster,
        state,
        damage_taken=12,
        rng=SequenceRng([8]),  # 8 + CON 2 = 10
    )
    broken = service.check_after_damage(
        caster,
        state,
        damage_taken=30,
        rng=SequenceRng([10]),  # 10 + CON 2 = 12 vs DC 15
    )

    assert maintained.outcome == ConcentrationOutcome.MAINTAINED
    assert maintained.state == state
    assert maintained.save_dc == 10
    assert maintained.save_total == 10
    assert broken.outcome == ConcentrationOutcome.BROKEN
    assert broken.previous == state
    assert broken.save_dc == 15
    assert broken.save_total == 12


def test_effect_definition_reports_concentration_duration() -> None:
    assert concentration_effect().starts_concentration is True

