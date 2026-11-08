# IKEA BILRESA scroll wheel (Matter)

[![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FAnalyticsEarth%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea%2Fbilresa-scroll-wheel.yaml)

Blueprint: [`blueprints/automation/ikea/bilresa-scroll-wheel.yaml`](../../blueprints/automation/ikea/bilresa-scroll-wheel.yaml)

For the IKEA BILRESA scroll wheel remote (E2490) paired directly to Home
Assistant over Matter (Thread).

## How the wheel appears in Home Assistant

The wheel has **3 channels**, and you switch between them on the remote. Each
channel is three Matter generic switches, so the device has **9 event
entities**:

| Channel | Clockwise | Counter-clockwise | Press |
| --- | --- | --- | --- |
| 1 | `…_1` | `…_2` | `…_3` |
| 2 | `…_4` | `…_5` | `…_6` |
| 3 | `…_7` | `…_8` | `…_9` |

Create **one automation per channel** you want to use. For example, channel 1
could control the living room lights and channel 2 could cycle scenes. To
mirror several wheels, add the matching entity from each wheel to the same
field.

## Gestures

| Input | Gesture | Matter event | Default (lights selected) |
| --- | --- | --- | --- |
| Clockwise | Rotate N notches | `multi_press_N` | Brightness +N × step (or colour temperature / next scene) |
| Counter-clockwise | Rotate N notches | `multi_press_N` | Brightness −N × step, stops at minimum (or colour temperature / previous scene) |
| Press | Press | `multi_press_1` | Toggle: all off if any light is on, otherwise all on |
| Press | Double press | `multi_press_2` | 100 % brightness |
| Press | Triple press | `multi_press_3` | Scene / custom action only |
| Press | Hold | `long_press` | Scene / custom action only |
| Press | Release | `long_release` | Custom action only |

*Rotation controls* chooses brightness, colour temperature or scene cycle. A
custom action for clockwise/counter-clockwise overrides that choice. Custom
actions receive `steps`, the number of notches turned.

## Limitations (Home Assistant Matter integration)

- **Rotation arrives after the wheel stops.** Home Assistant reports a single
  "N presses" event once you stop turning. It does not stream updates while
  the wheel is moving, so brightness changes in one step at the end of the
  turn.
- **Turns longer than 8 notches are dropped.** Home Assistant only creates
  `multi_press_1`–`multi_press_8`. Longer bursts are silently discarded
  ([home-assistant/core#159035](https://github.com/home-assistant/core/issues/159035)).
  Turn in shorter flicks, or raise *Brightness per notch*.
- Smooth real-time scrolling currently needs a custom integration such as
  [ha-ikea-bilresa](https://github.com/Vituhlos/ha-ikea-bilresa). This
  blueprint will be updated if Home Assistant adds native support.
- **Phantom events at startup:** see the *Advanced → Uptime sensor* option.

## Custom action variables

| Variable | Values |
| --- | --- |
| `button` | `cw`, `ccw`, `press` |
| `gesture` | `rotate`, `single`, `double`, `triple`, `hold`, `release` |
| `steps` | Notches turned (1–8) for rotation, otherwise `1` |
| `trigger` | The full state trigger |
