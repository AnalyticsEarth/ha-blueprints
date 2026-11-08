# IKEA BILRESA dual button (Matter)

[![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FAnalyticsEarth%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea%2Fbilresa-dual-button.yaml)

Blueprint: [`blueprints/automation/ikea/bilresa-dual-button.yaml`](../../blueprints/automation/ikea/bilresa-dual-button.yaml)

For the IKEA BILRESA dual button remote (E2489) paired directly to Home
Assistant over Matter (Thread).

## Setup

1. Commission the BILRESA in Home Assistant (*Settings → Devices & services →
   Add integration → Matter*). This needs a Thread border router.
2. The remote shows two **event** entities, usually ending in `_1` and `_2`.
   Press each button to see which is which.
3. Create an automation from the blueprint. Put each remote's first button in
   *Button 1* and its second button in *Button 2*. To mirror several remotes,
   add all of their button 1 entities to *Button 1*, and so on.

## Gestures

| Button | Gesture | Matter event | Default (lights selected) |
| --- | --- | --- | --- |
| 1 | Press | `multi_press_1` | Lights on |
| 1 | Double press | `multi_press_2` | Next scene in cycle, else 100 % brightness |
| 1 | Hold | `long_press` | Brighten until released |
| 1 | Release | `long_release` | Stop (custom action optional) |
| 2 | Press | `multi_press_1` | Lights off |
| 2 | Double press | `multi_press_2` | Previous scene in cycle, else minimum brightness (lights already on) |
| 2 | Hold | `long_press` | Dim until released (stops at minimum) |
| 2 | Release | `long_release` | Stop (custom action optional) |

For every gesture: **custom action → scene → default**.

## Notes

- Because the remote supports double press, Matter waits briefly after a
  press to check for a second one. Single presses therefore fire a moment
  after you release the button. This delay is in the device and Home
  Assistant, not in the blueprint.
- **Phantom presses at startup:** see the *Advanced → Uptime sensor* option
  ([home-assistant/core#129041](https://github.com/home-assistant/core/issues/129041)).
- The first press after a remote is newly added is ignored, because the
  entity has no previous state yet.

## Custom action variables

| Variable | Values |
| --- | --- |
| `button` | `b1`, `b2` |
| `gesture` | `single`, `double`, `hold`, `release` |
| `trigger` | The full state trigger |
