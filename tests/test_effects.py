import pytest

from dnd_combat_engine.models import EffectKind, EffectResolution, TargetKind, TargetReference


def test_target_reference_round_trips_to_plain_data() -> None:
    target = TargetReference("goblin", "Goblin", TargetKind.MONSTER, "goblin")

    assert TargetReference.from_dict(target.to_dict()) == target


def test_target_reference_rejects_missing_fields() -> None:
    with pytest.raises(ValueError):
        TargetReference("", "Goblin", TargetKind.MONSTER, "goblin")
    with pytest.raises(ValueError):
        TargetReference("goblin", "", TargetKind.MONSTER, "goblin")
    with pytest.raises(ValueError):
        TargetReference("goblin", "Goblin", TargetKind.MONSTER, "")


def test_effect_resolution_message_includes_target_and_total() -> None:
    target = TargetReference("ally", "Ally", TargetKind.CHARACTER, "ally")
    resolution = EffectResolution(
        source_name="Ravenisis",
        effect_name="Guiding Bolt",
        effect_kind=EffectKind.DAMAGE,
        target=target,
        total=14,
        detail="Applied 14 damage.",
    )

    assert resolution.message() == (
        "Ravenisis resolves Guiding Bolt on Ally [damage]. "
        "Total 14. Applied 14 damage."
    )
