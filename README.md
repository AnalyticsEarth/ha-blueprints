# Home Assistant Blueprints

Blueprints and other reusable Home Assistant content from
[AnalyticsEarth](https://github.com/AnalyticsEarth). It starts with IKEA Matter
remotes and will grow from there.

Every blueprint is tested against a real Home Assistant instance in CI (see
[`tests/`](tests)).

## Blueprints

### IKEA remotes (Matter)

| Device | Connection | What it does | Import |
| --- | --- | --- | --- |
| [BILRESA dual button](docs/ikea/bilresa-dual-button.md) | Matter over Thread | On / off, hold to dim, double press for scenes | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FAnalyticsEarth%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea%2Fbilresa-dual-button.yaml) |
| [BILRESA scroll wheel](docs/ikea/bilresa-scroll-wheel.md) | Matter over Thread | Scroll for brightness, colour temperature or scenes; press to toggle | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FAnalyticsEarth%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea%2Fbilresa-scroll-wheel.yaml) |
| [STYRBAR 4-button remote](docs/ikea/styrbar-remote.md) | DIRIGERA Matter bridge | On / off, hold to dim, left / right for scenes or colour temperature | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FAnalyticsEarth%2Fha-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea%2Fstyrbar-remote.yaml) |

All remote blueprints share the same design:

- **Mirroring:** each button field accepts several entities, so any number of
  remotes can control the same thing.
- **Layered overrides:** every gesture runs a *custom action* if you set one,
  otherwise a *scene* if you pick one, otherwise the default light behaviour.
- **Scene cycle:** list scenes to step through. The position comes from each
  scene's "last activated" time, so no helper entities are needed.
- **Safe dimming:** dimming stops at a minimum brightness instead of
  switching lights off, and lights that are off stay off when dimming down.
- **Matter quirks handled:** ignores unavailable/restore transitions, can
  debounce duplicate events, and can optionally ignore replayed events for 60
  seconds after Home Assistant starts (using the
  [Uptime](https://www.home-assistant.io/integrations/uptime/) sensor).

## Installing a blueprint

1. Click the **Import** button above. It opens your Home Assistant instance.
   Alternatively, go to *Settings → Automations & Scenes → Blueprints →
   Import Blueprint* and paste the blueprint's GitHub URL.
2. Create an automation from the blueprint and choose your remote's button
   entities.

To update, re-import the same URL. Home Assistant asks before overwriting.

## Repository layout

```text
blueprints/
  automation/<vendor>/   automation blueprints, grouped by vendor/device family
  script/                script blueprints
  template/              template entity blueprints
docs/<vendor>/           one page per blueprint: setup, entity mapping, quirks
tests/                   pytest suite that runs every blueprint in Home Assistant
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the conventions new content follows.

## Development

```bash
uv sync --group test
uv run yamllint .
uv run pytest
```

## License

[MIT](LICENSE)
