"""Behaviour tests for blueprints/automation/ikea/styrbar-remote.yaml."""

import asyncio
from datetime import timedelta

BP = "ikea/styrbar-remote.yaml"
UPDOWN = ["initial_press", "short_release", "long_press", "long_release"]
LEFTRIGHT = ["initial_press"]


async def _setup(ha, **inputs):
    for n in (1, 2):
        ha.add_button(f"event.styrbar{n}_up", UPDOWN)
        ha.add_button(f"event.styrbar{n}_down", UPDOWN)
        ha.add_button(f"event.styrbar{n}_left", LEFTRIGHT)
        ha.add_button(f"event.styrbar{n}_right", LEFTRIGHT)
    ha.light("light.a", brightness=128, color_temp_kelvin=3000)
    ha.light("light.b", "off")
    base = {
        "up_buttons": ["event.styrbar1_up", "event.styrbar2_up"],
        "down_buttons": ["event.styrbar1_down", "event.styrbar2_down"],
        "left_buttons": ["event.styrbar1_left", "event.styrbar2_left"],
        "right_buttons": ["event.styrbar1_right", "event.styrbar2_right"],
        "lights": ["light.a", "light.b"],
    }
    base.update(inputs)
    await ha.setup(BP, base)


async def test_up_tap_turns_on_and_ignores_initial_press(ha):
    await _setup(ha)
    await ha.press("event.styrbar1_up", "initial_press")
    assert ha.count("light.turn_on") == 0
    await ha.press("event.styrbar1_up", "short_release", after=0.1)
    assert ha.count("light.turn_on") == 1
    assert ha.last("light.turn_on")["entity_id"] == ["light.a", "light.b"]


async def test_mirrored_remote_down_tap_turns_off(ha):
    await _setup(ha)
    await ha.press("event.styrbar2_down", "short_release")
    assert ha.count("light.turn_off") == 1


async def test_duplicate_event_is_debounced(ha):
    await _setup(ha)
    await ha.press("event.styrbar1_down", "short_release")
    await ha.press("event.styrbar1_down", "short_release", after=0.1)
    assert ha.count("light.turn_off") == 1
    await ha.press("event.styrbar1_down", "short_release", after=1)
    assert ha.count("light.turn_off") == 2


async def test_left_right_step_colour_temperature_without_scenes(ha):
    await _setup(ha)
    await ha.press("event.styrbar1_left", "initial_press")
    # light.b is off, so only light.a changes; 3000 - 500 = 2500
    assert ha.count("light.turn_on") == 1
    assert ha.last("light.turn_on")["color_temp_kelvin"] == 2500
    ha.light("light.a", brightness=128, color_temp_kelvin=3800)
    await ha.press("event.styrbar1_right", "initial_press")
    assert ha.last("light.turn_on")["color_temp_kelvin"] == 4000  # clamped to max


async def test_scene_cycle(ha):
    now = ha.now
    ha.hass.states.async_set("scene.a", (now - timedelta(hours=3)).isoformat())
    ha.hass.states.async_set("scene.b", (now - timedelta(hours=1)).isoformat())
    ha.hass.states.async_set("scene.c", "unknown")
    await _setup(ha, scene_cycle=["scene.a", "scene.b", "scene.c"])
    await ha.press("event.styrbar1_right", "initial_press")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.c"]
    await ha.press("event.styrbar1_left", "initial_press")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.a"]
    assert ha.count("light.turn_on") == 0


async def test_scene_cycle_wraps_around(ha):
    now = ha.now
    ha.hass.states.async_set("scene.a", (now - timedelta(hours=1)).isoformat())
    ha.hass.states.async_set("scene.b", (now - timedelta(hours=3)).isoformat())
    await _setup(ha, scene_cycle=["scene.a", "scene.b"])
    await ha.press("event.styrbar1_left", "initial_press")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.b"]


async def test_precedence_custom_then_scene_then_lights(ha):
    await _setup(
        ha,
        scene_up_tap="scene.evening",
        scene_down_tap="scene.night",
        action_down_tap=[{"action": "test.custom", "data": {"button": "{{ button }}"}}],
    )
    await ha.press("event.styrbar1_up", "short_release")
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.evening"]
    assert ha.count("light.turn_on") == 0
    await ha.press("event.styrbar1_down", "short_release")
    assert ha.count("test.custom") == 1
    assert ha.last("test.custom")["button"] == "down"
    assert ha.count("light.turn_off") == 0


async def test_hold_dims_until_release(ha):
    await _setup(ha, hold_interval=300)
    await ha.press("event.styrbar1_down", "initial_press")
    await ha.press("event.styrbar1_down", "long_press", after=0.5, block=False)
    # light.b is off and must not be switched on by dimming down
    assert ha.count("light.turn_on") == 1
    assert ha.last("light.turn_on") == {
        "entity_id": ["light.a"], "brightness": 102, "transition": 0.3}
    ha.light("light.a", brightness=102, color_temp_kelvin=3000)
    await asyncio.sleep(0.3)
    assert ha.count("light.turn_on") == 2
    assert ha.last("light.turn_on")["brightness"] == 76
    await ha.press("event.styrbar1_down", "long_release", after=0.5)
    calls = ha.count("light.turn_on")
    await asyncio.sleep(0.7)
    assert ha.count("light.turn_on") == calls


async def test_hold_down_stops_at_minimum(ha):
    await _setup(ha, min_brightness=10)
    ha.light("light.a", brightness=30)
    await ha.press("event.styrbar1_down", "long_press")
    assert ha.last("light.turn_on")["brightness"] == 26  # 10% floor


async def test_ignores_unavailable_transitions(ha):
    await _setup(ha)
    ha.hass.states.async_set("event.styrbar1_down", "unavailable", {})
    await ha.hass.async_block_till_done()
    ha.hass.states.async_set(
        "event.styrbar1_down", ha.now.isoformat(),
        {"event_types": UPDOWN, "event_type": "short_release"})
    await ha.hass.async_block_till_done()
    assert ha.count("light.turn_off") == 0


async def test_startup_grace_with_uptime_sensor(ha):
    ha.hass.states.async_set("sensor.uptime", ha.now.isoformat(),
                             {"device_class": "timestamp"})
    await _setup(ha, uptime_sensor="sensor.uptime")
    await ha.press("event.styrbar1_down", "short_release")
    assert ha.count("light.turn_off") == 0


async def test_only_up_down_configured(ha):
    ha.add_button("event.styrbar1_up", UPDOWN)
    ha.add_button("event.styrbar1_down", UPDOWN)
    ha.light("light.a", brightness=128)
    await ha.setup(BP, {"up_buttons": ["event.styrbar1_up"],
                        "down_buttons": ["event.styrbar1_down"],
                        "lights": ["light.a"]})
    await ha.press("event.styrbar1_up", "short_release")
    assert ha.count("light.turn_on") == 1
