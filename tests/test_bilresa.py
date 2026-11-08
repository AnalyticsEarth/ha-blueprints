"""Behaviour tests for the BILRESA dual button and scroll wheel blueprints."""

import asyncio
from datetime import timedelta

DUAL = "ikea/bilresa-dual-button.yaml"
WHEEL = "ikea/bilresa-scroll-wheel.yaml"
PRESS_TYPES = ["multi_press_1", "multi_press_2", "multi_press_3", "long_press", "long_release"]
ROTATE_TYPES = [f"multi_press_{n}" for n in range(1, 9)]


# --------------------------------------------------------------- dual button
async def _dual(ha, **inputs):
    for remote in ("a", "b"):
        ha.add_button(f"event.bilresa_{remote}_button_1", PRESS_TYPES)
        ha.add_button(f"event.bilresa_{remote}_button_2", PRESS_TYPES)
    ha.light("light.a", brightness=128, color_temp_kelvin=3000)
    ha.light("light.b", "off")
    base = {
        "button1": ["event.bilresa_a_button_1", "event.bilresa_b_button_1"],
        "button2": ["event.bilresa_a_button_2", "event.bilresa_b_button_2"],
        "lights": ["light.a", "light.b"],
    }
    base.update(inputs)
    await ha.setup(DUAL, base)


async def test_dual_single_presses_on_off_from_either_remote(ha):
    await _dual(ha)
    await ha.press("event.bilresa_a_button_1", "multi_press_1")
    assert ha.count("light.turn_on") == 1
    await ha.press("event.bilresa_b_button_2", "multi_press_1")
    assert ha.count("light.turn_off") == 1
    # a second identical press is not debounced by default
    await ha.press("event.bilresa_b_button_2", "multi_press_1", after=0.1)
    assert ha.count("light.turn_off") == 2


async def test_dual_double_press_defaults(ha):
    await _dual(ha)
    await ha.press("event.bilresa_a_button_1", "multi_press_2")
    assert ha.last("light.turn_on")["brightness_pct"] == 100
    await ha.press("event.bilresa_a_button_2", "multi_press_2")
    # only lights that are on are dimmed to the minimum
    assert ha.last("light.turn_on") == {
        "entity_id": ["light.a"], "brightness_pct": 1, "transition": 0.5}


async def test_dual_double_press_cycles_scenes(ha):
    ha.hass.states.async_set("scene.a", (ha.now - timedelta(hours=1)).isoformat())
    ha.hass.states.async_set("scene.b", "unknown")
    await _dual(ha, scene_cycle=["scene.a", "scene.b"])
    await ha.press("event.bilresa_a_button_1", "multi_press_2")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.b"]
    assert ha.count("light.turn_on") == 0


async def test_dual_scene_and_custom_override(ha):
    await _dual(
        ha,
        scene_b1_single="scene.bright",
        action_b2_single=[{"action": "test.custom",
                           "data": {"g": "{{ button }}-{{ gesture }}"}}],
    )
    await ha.press("event.bilresa_a_button_1", "multi_press_1")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.bright"]
    await ha.press("event.bilresa_a_button_2", "multi_press_1")
    assert ha.last("test.custom")["g"] == "b2-single"
    assert ha.count("light.turn_on") == 0
    assert ha.count("light.turn_off") == 0


async def test_dual_hold_brightens_until_release(ha):
    await _dual(ha, hold_interval=300)
    await ha.press("event.bilresa_a_button_1", "long_press", block=False)
    # both lights brighten; light.b (off) starts from 0
    assert ha.count("light.turn_on") == 2
    briefs = {c.data["entity_id"][0]: c.data["brightness"] for c in ha.calls["light.turn_on"]}
    assert briefs == {"light.a": 154, "light.b": 26}
    await ha.press("event.bilresa_a_button_1", "long_release", after=0.1)
    calls = ha.count("light.turn_on")
    await asyncio.sleep(0.5)
    assert ha.count("light.turn_on") == calls


async def test_dual_without_lights_does_nothing(ha):
    await _dual(ha, lights=[])
    await ha.press("event.bilresa_a_button_1", "multi_press_1")
    await ha.press("event.bilresa_a_button_1", "long_press")
    assert sum(len(c) for c in ha.calls.values()) == 0


# --------------------------------------------------------------- scroll wheel
async def _wheel(ha, **inputs):
    for remote in ("a", "b"):
        for n in (1, 2):
            ha.add_button(f"event.wheel_{remote}_button_{n}", ROTATE_TYPES)
        ha.add_button(f"event.wheel_{remote}_button_3", PRESS_TYPES)
    ha.light("light.a", brightness=128, color_temp_kelvin=3000)
    ha.light("light.b", "off")
    base = {
        "cw_entities": ["event.wheel_a_button_1", "event.wheel_b_button_1"],
        "ccw_entities": ["event.wheel_a_button_2", "event.wheel_b_button_2"],
        "press_entities": ["event.wheel_a_button_3", "event.wheel_b_button_3"],
        "lights": ["light.a", "light.b"],
    }
    base.update(inputs)
    await ha.setup(WHEEL, base)


async def test_wheel_rotation_scales_with_notches(ha):
    await _wheel(ha)
    await ha.press("event.wheel_a_button_2", "multi_press_4",
                   totalNumberOfPressesCounted=4)
    # 4 notches x 5% down = -51 on the 0-255 scale; light.b is off so untouched
    assert ha.count("light.turn_on") == 1
    assert ha.last("light.turn_on")["brightness"] == 77
    await ha.press("event.wheel_b_button_1", "multi_press_2")  # mirrored wheel
    assert ha.count("light.turn_on") == 3
    assert {c.data["entity_id"][0]: c.data["brightness"]
            for c in ha.calls["light.turn_on"][1:]} == {"light.a": 154, "light.b": 26}


async def test_wheel_colour_temperature_mode(ha):
    await _wheel(ha, rotate_mode="color_temp")
    await ha.press("event.wheel_a_button_1", "multi_press_3")
    assert ha.last("light.turn_on")["color_temp_kelvin"] == 3450


async def test_wheel_scene_cycle_mode(ha):
    ha.hass.states.async_set("scene.a", (ha.now - timedelta(hours=1)).isoformat())
    ha.hass.states.async_set("scene.b", (ha.now - timedelta(hours=2)).isoformat())
    ha.hass.states.async_set("scene.c", "unknown")
    await _wheel(ha, rotate_mode="scene_cycle", scene_cycle=["scene.a", "scene.b", "scene.c"])
    await ha.press("event.wheel_a_button_2", "multi_press_5")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.c"]


async def test_wheel_press_toggles_group(ha):
    await _wheel(ha)
    await ha.press("event.wheel_a_button_3", "multi_press_1")
    assert ha.count("light.turn_off") == 1  # light.a was on
    ha.light("light.a", "off")
    await ha.press("event.wheel_a_button_3", "multi_press_1")
    assert ha.count("light.turn_on") == 1
    await ha.press("event.wheel_a_button_3", "multi_press_2")
    assert ha.last("light.turn_on")["brightness_pct"] == 100


async def test_wheel_custom_rotation_gets_steps(ha):
    await _wheel(ha, action_cw=[{"action": "test.custom",
                                 "data": {"steps": "{{ steps }}"}}],
                 scene_triple="scene.party")
    await ha.press("event.wheel_a_button_1", "multi_press_6")
    assert ha.last("test.custom")["steps"] == 6
    assert ha.count("light.turn_on") == 0
    await ha.press("event.wheel_a_button_3", "multi_press_3")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.party"]


async def test_wheel_without_press_entities(ha):
    await _wheel(ha, press_entities=[])
    await ha.press("event.wheel_a_button_1", "multi_press_1")
    assert ha.count("light.turn_on") == 2
    await ha.press("event.wheel_a_button_3", "multi_press_1")
    assert ha.count("light.turn_off") == 0
