"""Concrete combat feature plugins."""

from __future__ import annotations

from dataclasses import replace

from dnd_combat_engine.engine.attacks import AttackRequest
from dnd_combat_engine.engine.events import EngineEvent
from dnd_combat_engine.models.damage import DamageComponent, DamageType


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


class DivineSmiteFeature:
    """Spend a spell slot to add Divine Smite radiant damage."""

    name = "divine-smite"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return (
            event.name == "attack.started"
            and "Divine Smite" in request.active_features
            and "Divine Smite" in request.attacker.features
        )

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Spend the requested spell slot and add radiant damage."""
        request = _request_from_event(event)
        slot_level = _smite_slot_level(request, event)
        resource = request.attacker.resources.get(f"spell_slot_{slot_level}")
        if resource is not None and not resource.expend():
            return event
        dice_count = min(5, 1 + slot_level)
        return _with_request(
            event,
            _add_extra_damage(request, DamageComponent(f"{dice_count}d8", DamageType.RADIANT)),
        )


class GreatWeaponMasterFeature:
    """Apply Great Weapon Master's power attack tradeoff."""

    name = "great-weapon-master"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return (
            event.name == "attack.started"
            and "Great Weapon Master" in request.active_features
            and "Great Weapon Master" in request.attacker.features
        )

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Apply -5 to hit and +10 to damage."""
        request = _request_from_event(event)
        return _with_request(
            event,
            replace(
                request,
                attack_bonus=request.attack_bonus - 5,
                damage_bonus=request.damage_bonus + 10,
            ),
        )


class HexFeature:
    """Add Hex necrotic damage when requested for an attack."""

    name = "hex"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return (
            event.name == "attack.started"
            and "Hex" in request.active_features
            and "Hex" in request.attacker.features
        )

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Add Hex extra necrotic damage."""
        request = _request_from_event(event)
        return _with_request(
            event,
            _add_extra_damage(request, DamageComponent("1d6", DamageType.NECROTIC)),
        )


class RageFeature:
    """Add barbarian Rage melee damage."""

    name = "rage"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return (
            event.name == "attack.started"
            and "Rage" in request.active_features
            and "Rage" in request.attacker.features
        )

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Add a rage damage bonus scaled by barbarian level."""
        request = _request_from_event(event)
        return _with_request(
            event,
            replace(
                request,
                damage_bonus=request.damage_bonus + _rage_damage(request.attacker.level),
            ),
        )


class SharpshooterFeature:
    """Apply Sharpshooter's power attack tradeoff."""

    name = "sharpshooter"

    def applies_to(self, event: EngineEvent) -> bool:
        """Return whether this feature should handle an attack-started event."""
        request = _request_from_event(event)
        return (
            event.name == "attack.started"
            and "Sharpshooter" in request.active_features
            and "Sharpshooter" in request.attacker.features
        )

    def handle(self, event: EngineEvent) -> EngineEvent:
        """Apply -5 to hit and +10 to damage."""
        request = _request_from_event(event)
        return _with_request(
            event,
            replace(
                request,
                attack_bonus=request.attack_bonus - 5,
                damage_bonus=request.damage_bonus + 10,
            ),
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


def _rage_damage(level: int) -> int:
    if level >= 16:
        return 4
    if level >= 9:
        return 3
    return 2


def _smite_slot_level(request: AttackRequest, event: EngineEvent) -> int:
    if "smite_slot_level" in event.payload:
        return max(1, int(event.payload["smite_slot_level"]))
    available = [
        int(name.removeprefix("spell_slot_"))
        for name, resource in request.attacker.resources.items()
        if name.startswith("spell_slot_") and resource.current > 0
    ]
    return max(available, default=1)
