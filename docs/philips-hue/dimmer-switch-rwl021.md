# Philips Hue dimmer switch RWL020 / RWL021 (Hue Bridge)

[![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FAnalyticsEarth%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fphilips-hue%2Fdimmer-switch-rwl021.yaml)

Blueprint: [`blueprints/automation/philips-hue/dimmer-switch-rwl021.yaml`](../../blueprints/automation/philips-hue/dimmer-switch-rwl021.yaml)

For the original 4-button Philips Hue dimmer switch (RWL020 / RWL021: On,
Up, Down, Off) paired to a Hue Bridge, with the bridge added to Home Assistant
through the **Philips Hue** integration.

## Setup

1. In the Hue app, stop the bridge acting on the switch itself. Remove the
   switch's room or scene assignments so it doesn't control any lights.
   Otherwise the bridge and Home Assistant both react to every press.
2. In Home Assistant the switch shows four **event** entities: *Button 1* =
   On, *Button 2* = Up, *Button 3* = Down, *Button 4* = Off.
3. Create an automation from the blueprint and put each switch's buttons in
   the matching fields. To mirror several switches, add all their Button 1
   entities to *On*, and so on.

## Gestures

| Button | Gesture | Default (lights selected) |
| --- | --- | --- |
| On | Tap | Lights on. If they are already on and a scene cycle is set: next scene |
| On | Hold | 100 % brightness |
| Up | Tap | Brighter by the tap step |
| Up | Hold | Keep brightening until released |
| Down | Tap | Dimmer by the tap step (stops at minimum; lights that are off stay off) |
| Down | Hold | Keep dimming until released |
| Off | Tap | Lights off |
| Off | Hold | Scene / custom action only |

For every gesture: **custom action → scene → default**.

**Scene cycle:** this works like the Hue app. When the lights are off, On
re-activates the scene used most recently (or the *On scene* if you set one).
Each further On press steps to the next scene in the list.

## How the Hue Bridge reports presses

Recorded on a real RWL021 (Home Assistant 2026.11.0):

| Action | Events received |
| --- | --- |
| Tap | `initial_press`, then `short_release` about **1 s later** |
| Hold | `initial_press`; after ~1 s `long_press` + `repeat`; `repeat` about once a second; `long_release` |
| Quick double tap | Two complete taps, delivered within a millisecond of each other |

The bridge delivers button events in batches roughly a second apart. So by
default the blueprint runs taps as soon as `initial_press` arrives (*Advanced
→ Respond on press*) instead of waiting for the release. As in the Hue app,
holding a button therefore runs its tap action first. Turn the option off if
you'd rather wait for the release.

While Up / Down is held, the blueprint dims in its own smoother steps (every
400 ms by default) rather than once per `repeat`. Those steps continue until
`long_release` arrives. The automation runs in *queued* mode, so bunched
taps each run in turn and a double tap steps the scene cycle twice.

The same capture is replayed in [`tests/test_hue.py`](../../tests/test_hue.py).

## Not covered

- **RWL022** (the newer dimmer switch with a combined power button and a
  "hue" button) has a different layout. It needs its own blueprint.
- Switches paired directly to Zigbee (ZHA / Zigbee2MQTT) rather than a Hue
  Bridge report events differently and won't appear in the entity pickers.

## Custom action variables

| Variable | Values |
| --- | --- |
| `button` | `on`, `up`, `down`, `off` |
| `gesture` | `tap`, `hold`, `release` |
| `trigger` | The full state trigger (e.g. `trigger.entity_id` tells you which switch) |
