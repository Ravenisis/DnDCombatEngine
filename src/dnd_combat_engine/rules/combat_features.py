"""Concrete combat feature plugins."""

from __future__ import annotations

from dataclasses import replace

from dnd_combat_engine.engine.attacks import AttackRequest
from dnd_combat_engine.engine.events import EngineEvent
from dnd_combat_engine.models.damage import DamageComponent


class BlessFeature:
    """Add Bless attack bonus dice when requested for an attack."""

    name = "bless"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return event.name == "attack.started" and "Bless" in request.active_features

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Add a 1d4 attack bonus die to the attack request."""
        request = _request_from_event(event)
        updated = replace(request, attack_bonus_dice=(*request.attack_bonus_dice, "1d4"))
        return _with_request(event, updated)


class HuntersMarkFeature:
    """Add Hunter's Mark damage when requested for an attack."""

    name = "hunters-mark"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return (
            event.name == "attack.started"
            and "Hunter's Mark" in request.active_features
            and "Hunter's Mark" in request.attacker.features
        )

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Add Hunter's Mark extra weapon-typed damage."""
        request = _request_from_event(event)
        damage_type = request.weapon.damage.components[0].damage_type
        return _with_request(event, _add_extra_damage(request, DamageComponent("1d6", damage_type)))


class SneakAttackFeature:
    """Add rogue Sneak Attack damage when requested for an attack."""

    name = "sneak-attack"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return (
            event.name == "attack.started"
            and "Sneak Attack" in request.active_features
            and "Sneak Attack" in request.attacker.features
        )

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Add Sneak Attack extra weapon-typed damage based on attacker level."""
        request = _request_from_event(event)
        dice_count = max(1, (request.attacker.level + 1) // 2)
        damage_type = request.weapon.damage.components[0].damage_type
        return _with_request(
            event,
            _add_extra_damage(request, DamageComponent(f"{dice_count}d6", damage_type)),
        )


def _request_from_event(event: EngineEvent) -> AttackRequest:
    request = event.payload.get("request")
    if not isinstance(request, AttackRequest):
        raise TypeError("attack event payload request must be an AttackRequest")
    return request


def _with_request(event: EngineEvent, request: AttackRequest) -> EngineEvent:
    return EngineEvent(event.name, {**event.payload, "request": request})


def _add_extra_damage(request: AttackRequest, component: DamageComponent) -> AttackRequest:
    return replace(request, extra_damage=(*request.extra_damage, component))
