import logging
import sys

from cryptography.fernet import InvalidToken

from custom_components.aqua_temp.models.exceptions import LoginError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import HomeAssistant

from .common.consts import DEFAULT_NAME, DOMAIN, INVALID_TOKEN_SECTION
from .managers.aqua_temp_config_manager import AquaTempConfigManager
from .managers.aqua_temp_coordinator import AquaTempCoordinator
from .managers.password_manager import PasswordManager

_LOGGER = logging.getLogger(__name__)


async def async_setup(_hass, _config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Shinobi Video component."""
    initialized = False

    try:
        entry_config = {key: entry.data[key] for key in entry.data}

        await PasswordManager.decrypt(hass, entry_config, entry.entry_id)

        config_manager = AquaTempConfigManager(hass, entry)
        await config_manager.initialize(entry_config)

        is_initialized = config_manager.is_initialized

        if is_initialized:
            coordinator = AquaTempCoordinator(hass, config_manager)

            hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

            if hass.is_running:
                await coordinator.initialize()

            else:
                hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_START, coordinator.on_home_assistant_start
                )

            _LOGGER.info("Finished loading integration")

        initialized = is_initialized

    except InvalidToken:
        _LOGGER.error(
            "Corrupted password or encryption key, "
            f"please follow steps in {INVALID_TOKEN_SECTION}"
        )

    except LoginError:
        _LOGGER.error(f"Failed to login {DEFAULT_NAME} API, cannot log integration")

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to load {DEFAULT_NAME}, error: {ex}, line: {line_number}"
        )

    return initialized


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading {DOMAIN} integration, Entry ID: {entry.entry_id}")

    coordinator: AquaTempCoordinator = hass.data[DOMAIN][entry.entry_id]

    await coordinator.config_manager.remove(entry.entry_id)

    platforms = coordinator.config_manager.platforms

    for platform in platforms:
        await hass.config_entries.async_forward_entry_unload(entry, platform)

    del hass.data[DOMAIN][entry.entry_id]

    return True
