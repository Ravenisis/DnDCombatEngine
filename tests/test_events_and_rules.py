from dnd_combat_engine.engine.events import AttackFinishedEvent, AttackStartedEvent, EngineEvent
from dnd_combat_engine.rules import Feature, FeatureEngine


class EchoFeature:
    name = "echo"

    def applies_to(self, event: EngineEvent) -> bool:
        return event.name == "attack.started"

    def handle(self, event: EngineEvent) -> EngineEvent:
        return EngineEvent(name=event.name, payload={**event.payload, "handled": True})


def test_attack_events_have_expected_names() -> None:
    started = AttackStartedEvent({"attacker": "rogue-1"})
    finished = AttackFinishedEvent()

    assert started.name == "attack.started"
    assert started.payload == {"attacker": "rogue-1"}
    assert finished.name == "attack.finished"
    assert finished.event_id


def test_feature_protocol_shape_can_handle_events() -> None:
    feature: Feature = EchoFeature()
    event = AttackStartedEvent()

    handled = feature.handle(event)

    assert feature.applies_to(event) is True
    assert handled.payload["handled"] is True


def test_feature_engine_runs_applicable_features_in_order() -> None:
    first: Feature = EchoFeature()
    second: Feature = EchoFeature()
    event = AttackStartedEvent()

    handled = FeatureEngine([first, second]).process(event)

    assert handled.payload["handled"] is True
