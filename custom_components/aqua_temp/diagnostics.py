"""Diagnostics support for Tuya."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback

from . import DOMAIN
from .aqua_temp_coordinator import AquaTempCoordinator
from .consts import DATA_ITEM_CONFIG

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Starting diagnostic tool")

    coordinator = hass.data[DOMAIN][entry.entry_id]

    return _async_get_diagnostics(hass, coordinator, entry)


@callback
def _async_get_diagnostics(
    hass: HomeAssistant, coordinator: AquaTempCoordinator, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Getting diagnostic information")

    data = coordinator.data

    data["disabled_by"] = entry.disabled_by
    data["disabled_polling"] = entry.pref_disable_polling

    if DATA_ITEM_CONFIG in data and CONF_PASSWORD in data[DATA_ITEM_CONFIG]:
        data[DATA_ITEM_CONFIG].pop(CONF_PASSWORD)

    return data
