"""Replays of event sequences captured from real devices on Home Assistant 2026.11.0.

Captured 2026-11-08 from a STYRBAR ("Remote Control N2") and a RODRET dimmer,
both via the DIRIGERA Matter bridge, and a BILRESA scroll wheel paired over
Thread. Entity names are generic; timings are the recorded gaps in seconds.
"""

import asyncio

STYRBAR_UPDOWN = ["initial_press", "short_release", "long_press", "long_release"]
STYRBAR_SIDE = ["initial_press"]
WHEEL_ROTATE = [f"multi_press_{n}" for n in range(1, 9)]
WHEEL_PRESS = ["multi_press_1", "multi_press_2", "multi_press_3", "long_press", "long_release"]


async def test_styrbar_capture(ha):
    ids = {b: f"event.remote_{b}" for b in ("top", "bottom", "left", "right")}
    for b in ("top", "bottom"):
        ha.add_button(ids[b], STYRBAR_UPDOWN)
    for b in ("left", "right"):
        ha.add_button(ids[b], STYRBAR_SIDE)
    ha.light("light.a", brightness=128, color_temp_kelvin=3000)
    await ha.setup("ikea/styrbar-remote.yaml", {
        "up_buttons": [ids["top"]], "down_buttons": [ids["bottom"]],
        "left_buttons": [ids["left"]], "right_buttons": [ids["right"]],
        "lights": ["light.a"]})

    # tap top: initial_press then short_release 5 ms later
    await ha.press(ids["top"], "initial_press", newPosition=1)
    await ha.press(ids["top"], "short_release", after=0.005, previousPosition=1)
    assert ha.count("light.turn_on") == 1

    # hold top: initial_press and long_press arrive together, release 1.35 s later
    await ha.press(ids["top"], "initial_press", after=10)
    await ha.press(ids["top"], "long_press", after=0.005, block=False)
    await asyncio.sleep(1.3)
    held = ha.count("light.turn_on") - 1
    assert 3 <= held <= 5  # one step per 400 ms
    await ha.press(ids["top"], "long_release", after=1.35)
    await asyncio.sleep(0.5)
    assert ha.count("light.turn_on") - 1 == held

    # tap bottom
    ha.reset()
    await ha.press(ids["bottom"], "initial_press", after=7)
    await ha.press(ids["bottom"], "short_release", after=0.004)
    assert ha.count("light.turn_off") == 1

    # tap left: initial_press only
    await ha.press(ids["left"], "initial_press", after=4.5)
    assert ha.last("light.turn_on")["color_temp_kelvin"] == 2500

    # hold left: the remote sends a *top* tap instead (documented quirk)
    ha.reset()
    await ha.press(ids["top"], "initial_press", after=6)
    await ha.press(ids["top"], "short_release", after=0.005)
    assert ha.count("light.turn_on") == 1
    assert "color_temp_kelvin" not in ha.last("light.turn_on")

    # tap right
    await ha.press(ids["right"], "initial_press", after=6)
    assert ha.last("light.turn_on")["color_temp_kelvin"] == 3500


async def test_scroll_wheel_capture(ha):
    cw, ccw, press = (f"event.wheel_button_{n}" for n in (1, 2, 3))
    ha.add_button(cw, WHEEL_ROTATE)
    ha.add_button(ccw, WHEEL_ROTATE)
    ha.add_button(press, WHEEL_PRESS)
    ha.light("light.a", brightness=128, color_temp_kelvin=3000)
    await ha.setup("ikea/bilresa-scroll-wheel.yaml", {
        "cw_entities": [cw], "ccw_entities": [ccw], "press_entities": [press],
        "lights": ["light.a"]})

    # slow 2-notch turn clockwise: one multi_press_1 per notch, ~0.7 s apart
    await ha.press(cw, "multi_press_1", totalNumberOfPressesCounted=1)
    assert ha.last("light.turn_on")["brightness"] == 154  # +10 %
    ha.light("light.a", brightness=154, color_temp_kelvin=3000)
    await ha.press(cw, "multi_press_1", after=0.73, totalNumberOfPressesCounted=1)
    assert ha.last("light.turn_on")["brightness"] == 180
    ha.light("light.a", brightness=180, color_temp_kelvin=3000)

    # slow 2-notch turn counter-clockwise
    await ha.press(ccw, "multi_press_1", after=2.4, totalNumberOfPressesCounted=1)
    await ha.press(ccw, "multi_press_1", after=0.73, totalNumberOfPressesCounted=1)
    assert ha.count("light.turn_on") == 4
    assert ha.last("light.turn_on")["brightness"] == 154

    # (a fast spin of more than 8 notches produced no event at all)

    # press, double press, hold + release
    ha.reset()
    await ha.press(press, "multi_press_1", after=8, totalNumberOfPressesCounted=1)
    assert ha.count("light.turn_off") == 1  # toggle: light was on
    await ha.press(press, "multi_press_2", after=1.5, totalNumberOfPressesCounted=2)
    assert ha.last("light.turn_on")["brightness_pct"] == 100
    await ha.press(press, "long_press", after=1.6)
    await ha.press(press, "long_release", after=1.4)
    assert ha.count("light.turn_on") == 1  # hold has no default action


async def test_first_press_on_never_used_button(ha):
    """A second wheel that had never been used: its entity state was 'unknown'."""
    press = "event.wheel2_button_3"
    ha.add_button("event.wheel2_button_1", WHEEL_ROTATE, state="unknown")
    ha.add_button("event.wheel2_button_2", WHEEL_ROTATE, state="unknown")
    ha.add_button(press, WHEEL_PRESS, state="unknown")
    ha.light("light.a", "off")
    await ha.setup("ikea/bilresa-scroll-wheel.yaml", {
        "cw_entities": ["event.wheel2_button_1"],
        "ccw_entities": ["event.wheel2_button_2"],
        "press_entities": [press], "lights": ["light.a"]})
    await ha.press(press, "multi_press_1", totalNumberOfPressesCounted=1)
    assert ha.count("light.turn_on") == 1


async def test_rodret_with_dual_button_blueprint(ha):
    """RODRET via DIRIGERA reports like STYRBAR up/down; the dual button blueprint handles it."""
    on, off = "event.rodret_button", "event.rodret_button_2"
    ha.add_button(on, STYRBAR_UPDOWN, state="unknown")
    ha.add_button(off, STYRBAR_UPDOWN, state="unknown")
    ha.light("light.a", brightness=128)
    await ha.setup("ikea/bilresa-dual-button.yaml", {
        "button1": [on], "button2": [off], "lights": ["light.a"]})

    await ha.press(on, "initial_press")
    await ha.press(on, "short_release", after=0.002)
    assert ha.count("light.turn_on") == 1
    await ha.press(off, "initial_press", after=2.9)
    await ha.press(off, "short_release", after=0.002)
    assert ha.count("light.turn_off") == 1

    await ha.press(on, "initial_press", after=3.8)
    await ha.press(on, "long_press", after=0.001, block=False)
    assert ha.count("light.turn_on") == 2
    assert ha.last("light.turn_on")["brightness"] == 154
    await ha.press(on, "long_release", after=2.5)
    calls = ha.count("light.turn_on")
    await asyncio.sleep(0.5)
    assert ha.count("light.turn_on") == calls
