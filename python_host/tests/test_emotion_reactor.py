"""Tests for emotion reactor smoothing and node command mapping."""

from python_host.vision.emotion_reactor import EmotionReactor


class DummyOSC:
    def __init__(self):
        self.sent = []

    def send_raw(self, target_name, address, args=None, source="auto"):
        self.sent.append(
            {
                "target": target_name,
                "address": address,
                "args": list(args or []),
                "source": source,
            }
        )
        return True


def test_reactor_defaults_to_rest_without_face():
    osc = DummyOSC()
    reactor = EmotionReactor(
        osc_sender=osc,
        get_selected_target=lambda: "sue_1",
        get_selected_node_type=lambda: "sue",
        no_face_timeout_ms=200,
        min_hold_ms=0,
        command_cooldown_ms=10,
    )

    data = reactor.update(perception={}, has_face=False)
    assert data["flower_emotion"] == "REST"


def test_reactor_enters_bloom_and_emits_sue_state():
    osc = DummyOSC()
    reactor = EmotionReactor(
        osc_sender=osc,
        get_selected_target=lambda: "sue_1",
        get_selected_node_type=lambda: "sue",
        min_hold_ms=0,
        command_cooldown_ms=1,
    )

    perception = {"vit_emotion": {"dominant": "happy", "confidence": 1.0, "scores": [0.0] * 7}}
    state = reactor.snapshot()
    for _ in range(4):
        state = reactor.update(perception=perception, has_face=True)

    assert state["flower_emotion"] in ("BLOOM", "SOOTHE", "ALERT")
    assert any(item["address"] == "/state" for item in osc.sent)


def test_reactor_alert_can_burst_quickly():
    osc = DummyOSC()
    reactor = EmotionReactor(
        osc_sender=osc,
        get_selected_target=lambda: "sue_1",
        get_selected_node_type=lambda: "sue",
        min_hold_ms=1500,
        command_cooldown_ms=1,
    )

    perception = {"vit_emotion": {"dominant": "angry", "confidence": 0.95, "scores": [0.0] * 7}}
    state = reactor.update(perception=perception, has_face=True)
    state = reactor.update(perception=perception, has_face=True)

    assert state["flower_emotion"] in ("ALERT", "BLOOM")
    assert any(item["address"] == "/state" for item in osc.sent)


def test_reactor_kait_maps_rest_to_stop():
    osc = DummyOSC()
    reactor = EmotionReactor(
        osc_sender=osc,
        get_selected_target=lambda: "kait_1",
        get_selected_node_type=lambda: "kait",
        no_face_timeout_ms=0,
        min_hold_ms=0,
        command_cooldown_ms=1,
    )

    reactor.update(perception={}, has_face=False)
    if osc.sent:
        assert osc.sent[-1]["address"] in ("/stop", "/motion")


def test_reactor_update_config_changes_values():
    osc = DummyOSC()
    reactor = EmotionReactor(
        osc_sender=osc,
        get_selected_target=lambda: "sue_1",
        get_selected_node_type=lambda: "sue",
    )
    cfg = reactor.update_config({"alert_gain": 2.3, "soothe_gain": 0.6, "hold_soothe_ms": 2200})
    assert abs(cfg["alert_gain"] - 2.3) < 1e-6
    assert abs(cfg["soothe_gain"] - 0.6) < 1e-6
    assert cfg["hold_soothe_ms"] == 2200


