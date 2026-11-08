# IKEA STYRBAR remote (Matter via DIRIGERA)

[![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FAnalyticsEarth%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea%2Fstyrbar-remote.yaml)

Blueprint: [`blueprints/automation/ikea/styrbar-remote.yaml`](../../blueprints/automation/ikea/styrbar-remote.yaml)

For the IKEA STYRBAR 4-button remote (E2001 / E2002) paired to an IKEA
DIRIGERA hub, with DIRIGERA added to Home Assistant through the **Matter**
integration (multi-admin / Matter bridge).

## Setup

1. Pair the STYRBAR to DIRIGERA in the IKEA Home smart app.
2. Share DIRIGERA with Home Assistant as a Matter bridge (IKEA app →
   *Integrations → Matter*), then add it in Home Assistant's Matter
   integration.
3. The STYRBAR appears as a device with the model name **Remote Control N2**.
   It has four **event** entities named *Top Button* (up), *Bottom Button*
   (down), *Left Button* and *Right Button*.
4. Create an automation from the blueprint. Put each remote's up / down /
   left / right entity in the matching field. To mirror several STYRBARs, add
   all their "up" entities to the up field, and so on.

## Gestures

| Button | Gesture | Matter event | Default (lights selected) |
| --- | --- | --- | --- |
| Up | Tap | `short_release` | Lights on |
| Up | Hold | `long_press` | Brighten until released |
| Up | Release | `long_release` | Stop (custom action optional) |
| Down | Tap | `short_release` | Lights off |
| Down | Hold | `long_press` | Dim until released (stops at minimum) |
| Down | Release | `long_release` | Stop (custom action optional) |
| Left | Tap | `initial_press` | Previous scene in cycle, else warmer colour temperature |
| Right | Tap | `initial_press` | Next scene in cycle, else cooler colour temperature |

For every gesture: **custom action → scene → default**. If you set a custom
action, it runs. Otherwise a scene runs if you picked one. Otherwise the
default above runs.

## Known quirks

- **Left / right only report taps** over the DIRIGERA bridge. There are no
  hold events, so they have no hold options.
- **Holding left or right sends an "up" tap.** This is remote firmware
  behaviour, and it turns the lights on. Tap left/right rather than holding.
- **Duplicate events:** DIRIGERA sometimes sends the same event twice.
  Identical events within 250 ms are ignored. You can change this under
  *Advanced*.
- **Phantom presses at startup:** Matter can replay the last button event
  when Home Assistant restarts
  ([home-assistant/core#129041](https://github.com/home-assistant/core/issues/129041)).
  Add the [Uptime](https://www.home-assistant.io/integrations/uptime/)
  integration and select its sensor under *Advanced* to ignore events for 60
  seconds after startup.

## Verified behaviour

Recorded on real hardware (Home Assistant 2026.11.0, DIRIGERA Matter bridge):

| Action on the remote | Events received |
| --- | --- |
| Tap top / bottom | `initial_press`, then `short_release` about 5 ms later |
| Hold top / bottom | `initial_press` and `long_press` together, then `long_release` when let go |
| Tap left / right | `initial_press` only |
| Hold left | A **top** `initial_press` + `short_release` (the quirk above) |

The same capture is replayed in
[`tests/test_real_capture.py`](../../tests/test_real_capture.py).

## Custom action variables

| Variable | Values |
| --- | --- |
| `button` | `up`, `down`, `left`, `right` |
| `gesture` | `tap`, `hold`, `release` |
| `trigger` | The full state trigger (e.g. `trigger.entity_id` tells you which remote) |
