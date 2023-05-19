import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .aqua_temp_api import AquaTempAPI
from .aqua_temp_config_manager import AquaTempConfigManager
from .aqua_temp_coordinator import AquaTempCoordinator
from .consts import DOMAIN, SUPPORTED_DOMAINS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Shinobi Video component."""
    initialized = False

    try:
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        if entry.entry_id not in hass.data[DOMAIN]:
            config_manager = AquaTempConfigManager(hass, entry)
            await config_manager.initialize()

            api = AquaTempAPI(hass, config_manager)
            await api.initialize()

            coordinator = AquaTempCoordinator(hass, api, config_manager)

            hass.data[DOMAIN][entry.entry_id] = coordinator

            await coordinator.async_config_entry_first_refresh()

            load = hass.config_entries.async_forward_entry_setup
            for domain in SUPPORTED_DOMAINS:
                await load(entry, domain)

        initialized = True

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load Aqua Temp, error: {ex}, line: {line_number}")

    return initialized


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    del hass.data[DOMAIN][entry.entry_id]

    return True
