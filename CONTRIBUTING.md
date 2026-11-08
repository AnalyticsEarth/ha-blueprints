# Conventions

These conventions keep the blueprints consistent as the collection grows.

## Where things go

| Content | Path | Docs |
| --- | --- | --- |
| Automation blueprint | `blueprints/automation/<vendor>/<device>.yaml` | `docs/<vendor>/<device>.md` |
| Script blueprint | `blueprints/script/<vendor-or-topic>/<name>.yaml` | `docs/<vendor-or-topic>/<name>.md` |
| Template blueprint | `blueprints/template/<vendor-or-topic>/<name>.yaml` | `docs/<vendor-or-topic>/<name>.md` |
| Tests | `tests/test_<vendor-or-topic>.py` | — |

File names are lowercase and use dashes. **Never rename or move a published
blueprint.** Users' imports point at the URL, so renaming breaks their
updates. If a redesign is needed, add a new file and deprecate the old one in
its description.

## Blueprint checklist

- `name`, `author: AnalyticsEarth`, a `description` with a link to the docs
  page, and a `source_url` pointing at `blob/main/...` so re-import works.
- `homeassistant.min_version` set to the oldest version the syntax needs
  (input sections need 2024.6, plural `triggers:`/`actions:` need 2024.10).
- Group inputs into sections: *Remotes / devices*, *Lights* (or the target),
  *Scenes*, *Custom actions* (collapsed) and *Advanced* (collapsed).
- Every optional input has a `default` so the blueprint loads with minimal
  setup.
- Remote blueprints:
  - accept `multiple: true` entity selectors so remotes can be mirrored;
  - resolve each gesture as custom action → scene → default behaviour;
  - ignore `unknown`/`unavailable` transitions;
  - offer the debounce and uptime-sensor options;
  - expose `button`, `gesture` and `trigger` (plus any device-specific
    values, e.g. `steps`) to custom actions.
- Add the blueprint to the table in `README.md` with an import badge, and add
  an entry to `CHANGELOG.md`.

## Tests

Each blueprint gets behaviour tests in `tests/`. The `ha` fixture
(`tests/conftest.py`) loads the blueprint into a real Home Assistant, simulates
Matter event entities and records the service calls made. Run them with:

```bash
uv sync --group test
uv run pytest
```

## Releases

Users import from `main`, so `main` is always releasable. Add each change to
`CHANGELOG.md` under the blueprint's name.
