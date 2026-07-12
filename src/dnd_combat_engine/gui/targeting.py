"""Target references and effect-target side effects for the GUI."""

from __future__ import annotations

from typing import Any, cast

from dnd_combat_engine.models import ParticipantKind, TargetKind, TargetReference


def target_references_for_character_ids(
    app: Any,
    character_ids: tuple[str, ...],
) -> tuple[TargetReference, ...]:
    """Build target references for a collection of character identifiers."""
    return tuple(character_target_reference_with_name(app, item) for item in character_ids)


def character_target_reference_with_name(app: Any, character_id: str) -> TargetReference:
    """Build a named character target reference."""
    character = app.characters.load(character_id)
    return TargetReference(
        target_id=character_id,
        name=character.name,
        kind=TargetKind.CHARACTER,
        source_id=character_id,
    )


def active_target_for_effect(app: Any, state: Any) -> TargetReference | None:
    """Resolve the GUI's active target against current persisted data."""
    if state is None or state.active_target is None:
        return None
    target = state.active_target
    if target.kind is TargetKind.CHARACTER:
        try:
            character = app.characters.load(target.source_id)
        except KeyError:
            return None
        return TargetReference(
            target_id=character.character_id,
            name=character.name,
            kind=TargetKind.CHARACTER,
            source_id=character.character_id,
        )
    if target.kind is TargetKind.MONSTER:
        try:
            monster = app.compendium.load_monster(target.source_id)
        except KeyError:
            return None
        return TargetReference(
            target_id=target.target_id,
            name=monster.name,
            kind=TargetKind.MONSTER,
            source_id=monster.monster_id,
        )
    return target


def active_character_target_id(app: Any, state: Any) -> str | None:
    """Return the active target id when the target is a character."""
    target = active_target_for_effect(app, state)
    if target is None or target.kind is not TargetKind.CHARACTER:
        return None
    return cast(str, target.source_id)


def apply_damage_to_target(app: Any, target: TargetReference, damage_total: int) -> str:
    """Apply damage to a character or encounter monster target."""
    if target.kind is TargetKind.MONSTER:
        return apply_damage_to_monster_target(app, target, damage_total)
    character = app.characters.load(target.source_id)
    dealt = character.hit_points.apply_damage(damage_total)
    app.characters.save(character)
    return (
        f"Applied {dealt} damage; HP "
        f"{character.hit_points.current}/{character.hit_points.maximum}."
    )


def apply_damage_to_monster_target(
    app: Any,
    target: TargetReference,
    damage_total: int,
) -> str:
    """Apply damage to the matching encounter participant."""
    try:
        encounter_ids = app.encounters.persistence_service.list_encounter_ids()
    except AttributeError:
        return "Encounter target HP tracking is unavailable."
    for encounter_id in encounter_ids:
        try:
            encounter = app.encounters.load(encounter_id)
        except KeyError:
            continue
        for participant in encounter.participants:
            if (
                participant.kind is ParticipantKind.MONSTER
                or getattr(participant.kind, "value", None) == ParticipantKind.MONSTER.value
            ) and (
                participant.participant_id == target.target_id
                and participant.source_id == target.source_id
            ):
                monster = app.compendium.load_monster(participant.source_id)
                maximum_hp = monster.hit_points.maximum * participant.quantity
                updated_participant, dealt = participant.apply_damage(damage_total, maximum_hp)
                app.encounters.save(encounter.with_participant(updated_participant))
                return (
                    f"Applied {dealt} damage; HP "
                    f"{updated_participant.current_hit_points}/{maximum_hp}."
                )
    return "Encounter target could not be found."


def character_target_reference(character_id: str) -> TargetReference:
    """Build a character target reference when only its id is available."""
    return TargetReference(
        target_id=character_id,
        name=character_id,
        kind=TargetKind.CHARACTER,
        source_id=character_id,
    )
