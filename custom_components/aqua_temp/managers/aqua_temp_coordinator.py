from datetime import timedelta
import logging

from homeassistant.components.climate import HVACMode
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..common.api_types import APIParam
from ..common.consts import (
    DATA_ITEM_CONFIG,
    DATA_ITEM_DEVICES,
    DATA_ITEM_LOGIN_DETAILS,
    DOMAIN,
)
from .aqua_temp_api import AquaTempAPI
from .aqua_temp_config_manager import AquaTempConfigManager

_LOGGER = logging.getLogger(__name__)


class AquaTempCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self,
        hass,
        api: AquaTempAPI,
        config_manager: AquaTempConfigManager,
    ):
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
    def api_status(self):
        return self._api.is_connected

    @property
    def config_manager(self):
        return self._config_manager

    @property
    def devices(self):
        return self._api.devices

    @property
    def login_details(self):
        return self._api.login_details

    @property
    def config_data(self):
        return self._config_manager.data

    def get_device(self, device_code: str) -> DeviceInfo:
        param_nickname = self._config_manager.get_api_param(APIParam.Nickname)
        param_device_id = self._config_manager.get_api_param(APIParam.DeviceId)
        param_custom_model = self._config_manager.get_api_param(APIParam.CustomModel)

        device_data = self.get_device_data(device_code)
        device_nickname = device_data.get(param_nickname)
        device_model = device_data.get(param_custom_model)
        device_id = device_data.get(param_device_id)

        if param_custom_model in device_data:
            device_model = device_data.get(param_custom_model)

        device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_nickname,
            model=device_model,
        )

        return device_info

    async def _async_update_data(self):
        """Fetch parameters from API endpoint.

        This is the place to pre-process the parameters to lookup tables
        so entities can quickly look up their parameters.
        """
        try:
            await self._api.update()

            return {
                DATA_ITEM_DEVICES: self._api.devices,
                DATA_ITEM_LOGIN_DETAILS: self._api.login_details,
                DATA_ITEM_CONFIG: self.config_data,
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    def get_temperature_unit(self, device_code: str):
        return self._config_manager.get_temperature_unit(device_code)

    async def set_hvac_mode(self, device_code: str, hvac_mode: HVACMode):
        await self._api.set_hvac_mode(device_code, hvac_mode)

        await self.async_request_refresh()

    async def set_temperature(self, device_code: str, temperature: float):
        await self._api.set_temperature(device_code, temperature)

        await self.async_request_refresh()

    async def set_fan_mode(self, device_code: str, fan_mode):
        await self._api.set_fan_mode(device_code, fan_mode)

        await self.async_request_refresh()

    async def set_temperature_unit(self, device_code: str, option: str):
        await self._config_manager.update_temperature_unit(device_code, option)

        await self.async_request_refresh()

    def get_device_data(self, device_code: str) -> dict | None:
        device_data = self._api.get_device_data(device_code)

        return device_data

    def get_device_target_temperature(self, device_code: str) -> float | None:
        target_temperature = self._api.get_device_target_temperature(device_code)

        return target_temperature

    def get_device_current_temperature(self, device_code: str) -> float | None:
        current_temperature = self._api.get_device_current_temperature(device_code)

        return current_temperature

    def get_device_minimum_temperature(self, device_code: str) -> float | None:
        minimum_temperature = self._api.get_device_minimum_temperature(device_code)

        return minimum_temperature

    def get_device_maximum_temperature(self, device_code: str) -> float | None:
        maximum_temperature = self._api.get_device_maximum_temperature(device_code)

        return maximum_temperature

    def get_device_hvac_mode(self, device_code: str) -> HVACMode:
        hvac_mode = self._api.get_device_hvac_mode(device_code)

        return hvac_mode

    def get_device_fan_mode(self, device_code: str) -> str:
        fan_mode = self._api.get_device_fan_mode(device_code)

        return fan_mode

    def get_device_power(self, device_code: str) -> bool:
        power = self._api.get_device_power(device_code)

        return power

    def get_hvac_modes(self, device_code: str) -> list[HVACMode]:
        modes = self._config_manager.get_hvac_modes(device_code)

        result = [HVACMode(mode) for mode in modes]

        return result

    def get_fan_modes(self, device_code: str) -> list[str]:
        modes = self._config_manager.get_fan_modes(device_code)

        return modes
