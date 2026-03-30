"""Tests for emotion reactor smoothing and node command mapping."""

import random

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
        assert osc.sent[-1]["address"] == "/stop"


def test_reactor_kait_rest_always_stop():
    reactor = EmotionReactor(osc_sender=DummyOSC())
    assert reactor._command_for("kait", "REST") == ("/stop", [])


def _norm_kait_cmd(cmd):
    addr, args = cmd
    return (addr, tuple(args))


def test_reactor_kait_active_random_from_motion_and_motor_pool():
    reactor = EmotionReactor(osc_sender=DummyOSC())
    bloom_ok = {("/motion", (2,)), ("/motion", (6,)), ("/motor", (200,))}
    alert_ok = {("/motion", (3,)), ("/motion", (4,)), ("/motor", (230,))}
    soothe_ok = {("/motion", (1,)), ("/motion", (5,)), ("/motor", (100,))}
    for seed in range(300):
        random.seed(seed)
        assert _norm_kait_cmd(reactor._command_for("kait", "BLOOM")) in bloom_ok
        random.seed(seed + 1)
        assert _norm_kait_cmd(reactor._command_for("kait", "ALERT")) in alert_ok
        random.seed(seed + 2)
        assert _norm_kait_cmd(reactor._command_for("kait", "SOOTHE")) in soothe_ok

    random.seed(0)
    bloom_seen = {_norm_kait_cmd(reactor._command_for("kait", "BLOOM")) for _ in range(80)}
    assert len(bloom_seen) == 3


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


def test_reactor_dispatches_to_multiple_targets():
    osc = DummyOSC()
    reactor = EmotionReactor(
        osc_sender=osc,
        get_target_devices=lambda: [
            {"name": "sue_1", "node_type": "sue"},
            {"name": "kait_1", "node_type": "kait"},
            {"name": "F7OWER_00", "node_type": "sylvie"},
        ],
        min_hold_ms=0,
        command_cooldown_ms=1,
    )

    perception = {"vit_emotion": {"dominant": "happy", "confidence": 0.95, "scores": [0.0] * 7}}
    reactor.update(perception=perception, has_face=True)
    reactor.update(perception=perception, has_face=True)

    targets = {item["target"] for item in osc.sent}
    assert "sue_1" in targets
    assert "kait_1" in targets
    assert "F7OWER_00" in targets


def test_sylvie_soothe_vs_rest_mapping():
    osc = DummyOSC()
    reactor = EmotionReactor(
        osc_sender=osc,
        get_target_devices=lambda: [{"name": "F7OWER_00", "node_type": "sylvie"}],
    )

    soothe = reactor._command_for("sylvie", "SOOTHE")
    rest = reactor._command_for("sylvie", "REST")
    assert soothe == ("/preset", [4])
    assert rest == ("/preset", [3])


