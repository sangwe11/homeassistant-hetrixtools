import asyncio
from datetime import timedelta
import logging
import re
import sys
from typing import Any, Callable, Dict, Optional

import aiohttp
import async_timeout
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

API_URL="https://api.hetrixtools.com/v1/{apiKey}/uptime/report/{monitorId}/"
REQUEST_TIMEOUT = 30

SCAN_INTERVAL = timedelta(minutes=1)

MONITOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ID): cv.string, vol.Optional(CONF_NAME): cv.string
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_MONITORS): vol.All(cv.ensure_list, [MONITOR_SCHEMA]),
    }
)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    sensors = [HetrixToolsMonitorSensor(monitor["id"]) for monitor in config[CONF_MONITORS]]
    async_add_entities(sensors, update_before_add=True)

class HetrixToolsMonitorSensor(Entity):
    """Representation of a HetrixTools monitor sensor."""

    def __init__(self, api_key: str, id_: str):
        super().__init__()
        self._id = id_
        self._api_key = api_key
        self._state = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.id_

    @property
    def state(self) -> Optional[str]:
        return self._state

    async def async_fetch_state(self):
        """async_fetch_state."""
        try:
            websession = async_get_clientsession(self.hass)
            with async_timeout.timeout(REQUEST_TIMEOUT):
                resp = await websession.get(API_URL.format(apiKey=self._api_key, monitorId=self._id))
            if resp.status != 200:
                _LOGGER.error(f"{resp.url} returned {resp.status}")
                return

            json_response = await resp.json()
            return json_response

        except Exception:
            _LOGGER.exception("Error updating HetrixTools data.")

    async def async_update(self):
        """Retrieve latest state."""
        self._state = await async_fetch_state()
