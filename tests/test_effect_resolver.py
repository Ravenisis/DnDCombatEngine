import pytest

from dnd_combat_engine.models import (
    ActionCost,
    DurationKind,
    DurationProfile,
    EffectDefinition,
    EffectInteraction,
    EffectKind,
    InteractionOutcomeKind,
    InteractionTrigger,
    ResourcePool,
    TargetKind,
    TargetProfile,
    TargetReference,
    TurnEconomy,
)
from dnd_combat_engine.rules import EffectPlan, EffectResolver


def test_effect_definition_round_trips_to_plain_data() -> None:
    effect = EffectDefinition(
        effect_id="cure-wounds-healing",
        name="Cure Wounds",
        effect_kind=EffectKind.HEALING,
        target_profile=TargetProfile.ONE_CREATURE,
        action_cost=ActionCost.ACTION,
        duration=DurationProfile(DurationKind.INSTANTANEOUS),
        resource_cost="spell_slot_1",
        dice="1d8+3",
        interactions=(
            EffectInteraction(
                "cure-wounds-heal",
                InteractionTrigger.ON_TARGET,
                InteractionOutcomeKind.APPLY_HEALING,
                label="Hit Points",
                value="1d8 + spellcasting modifier",
                scaling={
                    "mode": "spell_slot",
                    "base_spell_level": 1,
                    "per_slot_level_above_base": "+1d8 healing",
                },
            ),
        ),
    )

    assert EffectDefinition.from_dict(effect.to_dict()) == effect
    assert effect.requires_target is True
    assert effect.interactions[0].summary() == (
        "on target: apply healing Hit Points 1d8 + spellcasting modifier "
        "(scales +1d8 healing above level 1)."
    )


def test_effect_resolver_spends_action_resource_and_explains_resolution() -> None:
    target = TargetReference("ravenisis", "Ravenisis", TargetKind.CHARACTER, "ravenisis")
    effect = EffectDefinition(
        effect_id="cure-wounds-healing",
        name="Cure Wounds",
        effect_kind=EffectKind.HEALING,
        target_profile=TargetProfile.ONE_CREATURE,
        resource_cost="spell_slot_1",
        dice="1d8+3",
        interactions=(
            EffectInteraction(
                "cure-wounds-heal",
                InteractionTrigger.ON_TARGET,
                InteractionOutcomeKind.APPLY_HEALING,
                label="Hit Points",
                value="1d8 + spellcasting modifier",
            ),
        ),
    )
    resources = {"spell_slot_1": ResourcePool("spell_slot_1", current=1, maximum=4)}
    economy = TurnEconomy()

    result = EffectResolver().resolve(
        EffectPlan("Cleric", effect, targets=(target,), total=7, detail="Applied 7 healing."),
        economy=economy,
        resources=resources,
    )

    assert result.resource_spent == "spell_slot_1"
    assert result.action_spent is True
    assert resources["spell_slot_1"].current == 0
    assert economy.action_used is True
    assert result.messages == (
        "Cleric resolves Cure Wounds on Ravenisis [healing]. "
        "Total 7. Spent spell_slot_1. Dice 1d8+3. "
        "on target: apply healing Hit Points 1d8 + spellcasting modifier. "
        "Applied 7 healing.",
    )


def test_effect_resolver_rejects_missing_target_or_depleted_resource() -> None:
    effect = EffectDefinition(
        effect_id="guiding-bolt-damage",
        name="Guiding Bolt",
        effect_kind=EffectKind.DAMAGE,
        target_profile=TargetProfile.ONE_CREATURE,
        resource_cost="spell_slot_1",
    )

    with pytest.raises(ValueError, match="requires at least one target"):
        EffectResolver().resolve(EffectPlan("Cleric", effect))

    target = TargetReference("goblin", "Goblin", TargetKind.MONSTER, "goblin")
    resources = {"spell_slot_1": ResourcePool("spell_slot_1", current=0, maximum=1)}
    with pytest.raises(ValueError, match="depleted"):
        EffectResolver().resolve(
            EffectPlan("Cleric", effect, targets=(target,)),
            resources=resources,
        )
