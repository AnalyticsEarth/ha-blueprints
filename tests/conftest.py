"""Shared fixtures: load a blueprint from this repo into a test Home Assistant."""

from __future__ import annotations

import asyncio
import shutil
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BLUEPRINTS = REPO_ROOT / "blueprints"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    """Allow loading integrations in tests."""


class Harness:
    """Drives Matter event entities and records service calls."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.now = dt_util.utcnow()
        self.calls: dict[str, list[ServiceCall]] = {}
        for service in ("light.turn_on", "light.turn_off", "light.toggle",
                        "scene.turn_on", "test.custom"):
            domain, name = service.split(".")
            self.calls[service] = async_mock_service(hass, domain, name)

    async def setup(self, path: str, inputs: dict[str, Any]) -> None:
        assert await async_setup_component(
            self.hass,
            "automation",
            {
                "automation": {
                    "id": "under_test",
                    "alias": "under test",
                    "use_blueprint": {"path": path, "input": inputs},
                }
            },
        )
        await self.hass.async_block_till_done()
        state = self.hass.states.get("automation.under_test")
        assert state is not None and state.state == "on", "automation failed to load"

    def add_button(self, entity_id: str, event_types: list[str]) -> None:
        """Create a Matter-style event entity with a restored (past) state."""
        self.hass.states.async_set(
            entity_id,
            (self.now - timedelta(days=1)).isoformat(),
            {"event_types": event_types, "event_type": None, "device_class": "button"},
        )

    async def press(self, entity_id: str, event_type: str, after: float = 1.0,
                    block: bool = True, **extra: Any) -> None:
        """Fire an event on an event entity `after` seconds after the last one."""
        self.now += timedelta(seconds=after)
        attrs = dict(self.hass.states.get(entity_id).attributes)
        attrs["event_type"] = event_type
        attrs.update(extra)
        self.hass.states.async_set(entity_id, self.now.isoformat(), attrs)
        if block:
            await self.hass.async_block_till_done()
        else:
            # let the run start without waiting for delays/loops to finish
            await asyncio.sleep(0.05)

    async def advance(self, seconds: float) -> None:
        """Move time forward so script delays complete."""
        async_fire_time_changed(self.hass, dt_util.utcnow() + timedelta(seconds=seconds))
        await self.hass.async_block_till_done()

    def light(self, entity_id: str, state: str = "on", **attrs: Any) -> None:
        base = {
            "supported_color_modes": ["color_temp"],
            "color_mode": "color_temp",
            "min_color_temp_kelvin": 2200,
            "max_color_temp_kelvin": 4000,
        }
        base.update(attrs)
        self.hass.states.async_set(entity_id, state, base)

    def count(self, service: str) -> int:
        return len(self.calls[service])

    def last(self, service: str) -> dict[str, Any]:
        return dict(self.calls[service][-1].data)

    def reset(self) -> None:
        for calls in self.calls.values():
            calls.clear()


@pytest.fixture
async def ha(hass: HomeAssistant, tmp_path: Path) -> Harness:
    shutil.copytree(BLUEPRINTS, tmp_path / "blueprints")
    hass.config.config_dir = str(tmp_path)
    return Harness(hass)
