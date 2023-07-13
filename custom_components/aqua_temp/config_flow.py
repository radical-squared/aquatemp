"""Config flow to configure."""
from __future__ import annotations

import hashlib
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector

from .common.api_types import API_TYPES
from .common.consts import CONF_API_TYPE, DEFAULT_NAME, DOMAIN
from .common.exceptions import LoginError
from .managers.aqua_temp_api import AquaTempAPI
from .managers.aqua_temp_config_manager import AquaTempConfigManager

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class DomainFlowHandler(config_entries.ConfigFlow):
    """Handle a domain config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        super().__init__()

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        _LOGGER.debug(f"Starting async_step_user of {DEFAULT_NAME}")

        errors = None

        if user_input is not None:
            try:
                password = user_input.get(CONF_PASSWORD)

                password_bytes = bytes(password, "utf-8")

                md5hash = hashlib.new("md5")
                md5hash.update(password_bytes)

                password_hashed = md5hash.hexdigest()

                user_input[CONF_PASSWORD] = password_hashed

                config_manager = AquaTempConfigManager(self.hass, None)
                config_manager.update_credentials(user_input)

                await config_manager.initialize()

                api = AquaTempAPI(self.hass, config_manager)

                await api.initialize(True)

                _LOGGER.debug("User inputs are valid")

                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

            except LoginError:
                errors = {"base": "invalid_credentials"}

            if errors is not None:
                error_message = errors.get("base")

                _LOGGER.warning(f"Failed to create integration, Error: {error_message}")

        new_user_input = {
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_API_TYPE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=API_TYPES,
                    translation_key=CONF_API_TYPE,
                ),
            ),
        }

        schema = vol.Schema(new_user_input)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
