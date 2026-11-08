"""Behaviour tests for blueprints/automation/philips-hue/dimmer-switch-rwl021.yaml.

Timings in the capture-based tests were recorded from a real RWL021 on a Hue
Bridge (Home Assistant 2026.11.0): the bridge delivers events in batches about
1 s apart, a hold sends long_press + repeat (~1/s) + long_release, and a quick
double tap arrives as two taps within a millisecond.
"""

import asyncio
from datetime import timedelta

from homeassistant.core import ServiceCall
from homeassistant.util import dt as dt_util

BP = "philips-hue/dimmer-switch-rwl021.yaml"
TYPES = ["initial_press", "repeat", "short_release", "long_press", "long_release"]
ON, UP, DOWN, OFF = (f"event.hue{n}_button_{b}" for n, b in ((1, 1), (1, 2), (1, 3), (1, 4)))


async def _setup(ha, **inputs):
    for n in (1, 2):
        for b in (1, 2, 3, 4):
            ha.add_button(f"event.hue{n}_button_{b}", TYPES)
    ha.light("light.a", brightness=128, color_temp_kelvin=3000)
    ha.light("light.b", "off")
    base = {
        "on_buttons": [ON, "event.hue2_button_1"],
        "up_buttons": [UP, "event.hue2_button_2"],
        "down_buttons": [DOWN, "event.hue2_button_3"],
        "off_buttons": [OFF, "event.hue2_button_4"],
        "lights": ["light.a", "light.b"],
    }
    base.update(inputs)
    await ha.setup(BP, base)


async def _tap(ha, entity, after=3.0):
    """A tap as delivered by the bridge: release ~1 s after the press."""
    await ha.press(entity, "initial_press", after=after)
    await ha.press(entity, "short_release", after=1.01)


def _live_scenes(ha):
    """Make scene.turn_on update the scene's state, like real scenes do."""
    calls = ha.calls["scene.turn_on"]

    async def handler(call: ServiceCall) -> None:
        calls.append(call)
        await asyncio.sleep(0.2)  # real scene calls take a moment
        for entity_id in call.data["entity_id"]:
            ha.hass.states.async_set(entity_id, dt_util.utcnow().isoformat())

    ha.hass.services.async_register("scene", "turn_on", handler)


async def test_tap_on_fires_on_press_only_once(ha):
    await _setup(ha)
    await ha.press(ON, "initial_press")
    assert ha.count("light.turn_on") == 1
    await ha.press(ON, "short_release", after=1.01)
    assert ha.count("light.turn_on") == 1


async def test_wait_for_release_when_fast_taps_off(ha):
    await _setup(ha, fast_taps=False)
    await ha.press(ON, "initial_press")
    assert ha.count("light.turn_on") == 0
    await ha.press(ON, "short_release", after=1.01)
    assert ha.count("light.turn_on") == 1


async def test_mirrored_switch_off(ha):
    await _setup(ha)
    await _tap(ha, "event.hue2_button_4")
    assert ha.count("light.turn_off") == 1


async def test_up_down_taps_step_brightness(ha):
    await _setup(ha)
    await _tap(ha, UP)
    calls = {c.data["entity_id"][0]: c.data["brightness"] for c in ha.calls["light.turn_on"]}
    assert calls == {"light.a": 154, "light.b": 26}
    ha.reset()
    await _tap(ha, DOWN)
    assert ha.count("light.turn_on") == 1  # light.b is off: not dimmed on
    assert ha.last("light.turn_on")["brightness"] == 102


async def test_on_cycles_scenes_like_hue_app(ha):
    _live_scenes(ha)
    now = ha.now
    ha.hass.states.async_set("scene.read", (now - timedelta(hours=2)).isoformat())
    ha.hass.states.async_set("scene.relax", (now - timedelta(hours=1)).isoformat())
    ha.hass.states.async_set("scene.night", "unknown")
    await _setup(ha, scene_cycle=["scene.read", "scene.relax", "scene.night"])
    # lights on: next scene after the last used one (relax -> night)
    await _tap(ha, ON)
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.night"]
    # double tap (two taps within a millisecond) steps twice: night -> read -> relax
    await ha.press(ON, "initial_press", after=3, block=False)
    await ha.press(ON, "short_release", after=1.011, block=False)
    ha.hass.states.async_set(ON, (ha.now + timedelta(seconds=0.001)).isoformat(),
                             {"event_types": TYPES, "event_type": "initial_press"})
    ha.now += timedelta(seconds=0.002)
    await ha.press(ON, "short_release", after=0)
    assert [c.data["entity_id"][0] for c in ha.calls["scene.turn_on"]] == [
        "scene.night", "scene.read", "scene.relax"]


async def test_on_when_lights_off_reactivates_last_scene(ha):
    now = ha.now
    ha.hass.states.async_set("scene.read", (now - timedelta(hours=2)).isoformat())
    ha.hass.states.async_set("scene.relax", (now - timedelta(hours=1)).isoformat())
    await _setup(ha, scene_cycle=["scene.read", "scene.relax"])
    ha.light("light.a", "off")
    await _tap(ha, ON)
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.relax"]
    assert ha.count("light.turn_on") == 0


async def test_on_scene_when_lights_off(ha):
    ha.hass.states.async_set("scene.read", ha.now.isoformat())
    await _setup(ha, scene_cycle=["scene.read"], scene_on_tap="scene.welcome")
    ha.light("light.a", "off")
    await _tap(ha, ON)
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.welcome"]


async def test_off_scene_and_custom_overrides(ha):
    await _setup(ha, scene_off_tap="scene.night",
                 action_up_tap=[{"action": "test.custom",
                                 "data": {"g": "{{ button }}-{{ gesture }}"}}])
    await _tap(ha, OFF)
    assert ha.last("scene.turn_on")["entity_id"] == ["scene.night"]
    assert ha.count("light.turn_off") == 0
    await _tap(ha, UP)
    assert ha.last("test.custom")["g"] == "up-tap"
    assert ha.count("light.turn_on") == 0


async def test_hold_on_goes_full_brightness(ha):
    await _setup(ha, fast_taps=False)
    await ha.press(ON, "initial_press")
    await ha.press(ON, "long_press", after=1.01)
    await ha.press(ON, "repeat", after=0.001)
    await ha.press(ON, "long_release", after=0.001)
    assert ha.count("light.turn_on") == 1
    assert ha.last("light.turn_on")["brightness_pct"] == 100


async def test_hold_down_capture(ha):
    """Recorded hold: press, long_press +1.0 s, repeat x3 ~1 s apart, release."""
    await _setup(ha, hold_interval=300)
    await ha.press(DOWN, "initial_press")  # fast tap step first: 128 -> 102
    assert ha.last("light.turn_on")["brightness"] == 102
    ha.light("light.a", brightness=102, color_temp_kelvin=3000)
    await ha.press(DOWN, "long_press", after=1.009, block=False)
    await ha.press(DOWN, "repeat", after=0.001, block=False)
    assert ha.count("light.turn_on") == 2
    assert ha.last("light.turn_on")["brightness"] == 76
    await asyncio.sleep(0.35)
    await ha.press(DOWN, "repeat", after=1.007, block=False)  # repeats don't restart
    await asyncio.sleep(0.3)
    steps = ha.count("light.turn_on")
    assert steps >= 4
    await ha.press(DOWN, "repeat", after=1.008, block=False)
    await ha.press(DOWN, "long_release", after=0.001, block=False)
    await asyncio.sleep(0.7)
    assert ha.count("light.turn_on") <= steps + 1  # at most the step in flight
    final = ha.count("light.turn_on")
    await asyncio.sleep(0.6)
    assert ha.count("light.turn_on") == final


async def test_only_on_button_configured(ha):
    ha.add_button(ON, TYPES)
    ha.light("light.a", "off")
    await ha.setup(BP, {"on_buttons": [ON], "lights": ["light.a"]})
    await _tap(ha, ON)
    assert ha.count("light.turn_on") == 1
