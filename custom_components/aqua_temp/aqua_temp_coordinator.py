from datetime import timedelta
import logging

import async_timeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .aqua_temp_api import AquaTempAPI
from .aqua_temp_config_manager import AquaTempConfigManager
from .consts import DATA_ITEM_API, DATA_ITEM_CONFIG

_LOGGER = logging.getLogger(__name__)


class AquaTempCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, api: AquaTempAPI, config_manager: AquaTempConfigManager):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=config_manager.name,
            update_interval=timedelta(seconds=30),
            update_method=self._async_update_data,
        )

        self._api = api
        self._config_manager = config_manager

    @property
    def api_data(self):
        return self.data.get(DATA_ITEM_API)

    @property
    def config_data(self):
        return self.data.get(DATA_ITEM_CONFIG)

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with async_timeout.timeout(10):
                await self._api.update()

                return {
                    DATA_ITEM_API: self._api.data,
                    DATA_ITEM_CONFIG: self._config_manager.data,
                }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def set_hvac_mode(self, hvac_mode):
        await self._api.set_hvac_mode(hvac_mode)

    async def set_temperature(self, hvac_mode, temperature):
        await self._api.set_temperature(hvac_mode, temperature)

    async def set_fan_mode(self, fan_mode):
        await self._api.set_fan_mode(fan_mode)
