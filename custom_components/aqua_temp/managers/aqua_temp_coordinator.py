from datetime import timedelta
import logging

import async_timeout

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..common.consts import DATA_ITEM_API, DATA_ITEM_CONFIG, DOMAIN
from .aqua_temp_api import AquaTempAPI
from .aqua_temp_config_manager import AquaTempConfigManager

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

    def get_device(self, device_code: str) -> DeviceInfo:
        device_data = self.api_data.get(device_code)
        device_nickname = device_data.get("device_nick_name", device_code)
        device_type = device_data.get("device_type")

        device_info = DeviceInfo(
            identifiers={(DOMAIN, self._config_manager.unique_id)},
            name=device_nickname,
            model=device_type,
        )

        return device_info

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

    def get_temperature_unit(self, device_code: str):
        return self._config_manager.get_temperature_unit(device_code)

    async def set_hvac_mode(self, device_code: str, hvac_mode):
        await self._api.set_hvac_mode(device_code, hvac_mode)

    async def set_temperature(self, device_code: str, hvac_mode, temperature):
        await self._api.set_temperature(device_code, hvac_mode, temperature)

    async def set_fan_mode(self, device_code: str, fan_mode):
        await self._api.set_fan_mode(device_code, fan_mode)

    async def set_temperature_unit(self, device_code: str, option: str):
        await self._config_manager.update_temperature_unit(device_code, option)
