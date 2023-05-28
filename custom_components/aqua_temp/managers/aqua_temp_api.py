"""Platform for climate integration."""
import logging
import sys

from aiohttp import ClientSession

from homeassistant.components.climate.const import HVAC_MODE_OFF, HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ..common.consts import (
    ALL_ENTITIES,
    CONTROL_PATH,
    DEVICELIST_PATH,
    FAN_MODE_MAPPING,
    GETDATABYCODE_PATH,
    GETDEVICESTATUS_PATH,
    GETFAULT_PATH,
    PRODUCT_IDS,
    HEADERS,
    HVAC_MODE_MAPPING,
    LOGIN_PATH,
    POWER_MODE_OFF,
    POWER_MODE_ON,
    SERVER_URL,
)
from ..common.exceptions import LoginError, OperationFailedException
from .aqua_temp_config_manager import AquaTempConfigManager

_LOGGER = logging.getLogger(__name__)


class AquaTempAPI:
    data: dict

    _session: ClientSession | None
    _config_manager: AquaTempConfigManager
    _token: str | None
    _hass: HomeAssistant | None

    def __init__(
        self, hass: HomeAssistant | None, config_manager: AquaTempConfigManager
    ):
        """Initialize the climate entity."""

        self.data = {}

        self._session = None
        self._token = None

        self._hass = hass
        self._headers = HEADERS
        self._config_manager = config_manager
        self.protocol_codes = []

    @property
    def is_connected(self):
        result = self._session is not None and self._token is not None

        return result

    async def initialize(self):
        try:
            if not self.is_connected:
                for entity_description in ALL_ENTITIES:
                    if (
                        entity_description.key not in self.protocol_codes
                        and entity_description.is_protocol_code
                    ):
                        self.protocol_codes.append(entity_description.key)

                if self._hass is None:
                    self._session = ClientSession()
                else:
                    self._session = async_create_clientsession(hass=self._hass)

                await self._login()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(
                f"Failed to initialize session, Error: {ex}, Line: {line_number}"
            )

    async def terminate(self):
        if self._hass is None:
            await self._session.close()

    async def validate(self):
        await self.initialize()

        if self._token is None:
            raise LoginError()

    async def update(self):
        """Fetch new state data for the sensor."""
        try:
            if not self.is_connected:
                await self.initialize()

            for device_code in self.data:
                _LOGGER.debug(f"Starting to update device: {device_code}")

                await self._fetch_data(device_code)

                await self._fetch_errors(device_code)
        except Exception as ex:
            self._token = None
            _LOGGER.error(f"Error fetching data. Reconnecting, Error: {ex}")

    async def set_hvac_mode(self, device_code: str, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self._set_power_mode(device_code, POWER_MODE_OFF)

        else:
            device_data = self.data.get(device_code)
            current_power = device_data.get("Power")

            is_on = current_power == POWER_MODE_ON

            if not is_on:
                await self._set_power_mode(device_code, POWER_MODE_ON)

            pc_hvac_mode = HVAC_MODE_MAPPING.get(hvac_mode)

            await self._set_hvac_mode(device_code, pc_hvac_mode)

    async def set_temperature(self, device_code: str, hvac_mode, temperature):
        """Set new target temperature."""
        hvac_mode_mapping = HVAC_MODE_MAPPING.get(hvac_mode)
        mode = f"R0{hvac_mode_mapping}"

        request_data = {mode: temperature, "Set_Temp": temperature}

        await self._perform_action(device_code, request_data)

    async def _set_power_mode(self, device_code: str, value):
        """Set new target power mode."""
        request_data = {"power": value}

        await self._perform_action(device_code, request_data)

    async def _set_hvac_mode(self, device_code: str, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            return

        value = HVAC_MODE_MAPPING.get(device_code, hvac_mode)

        request_data = {"mode": value}

        await self._perform_action(device_code, request_data)

    async def set_fan_mode(self, device_code: str, fan_mode):
        """Set new target fan mode."""

        value = FAN_MODE_MAPPING.get(fan_mode)

        request_data = {"Manual-mute": value}

        await self._perform_action(device_code, request_data)

    async def _perform_action(self, device_code: str, request_data: dict):
        params = self._get_request_params(device_code, request_data)

        data = {"param": params}

        operation_response = await self._post_request(CONTROL_PATH, data)

        error_msg = operation_response.get("error_msg")

        if error_msg != "Success":
            operation = list(data.keys())[0]
            value = data[operation]

            raise OperationFailedException(operation, value, error_msg)

    async def _fetch_data(self, device_code: str):
        data = self._get_request_params(device_code, self.protocol_codes)
        data_response = await self._post_request(GETDATABYCODE_PATH, data)
        object_result_items = data_response.get("object_result", [])

        for object_result_item in object_result_items:
            code = object_result_item.get("code")
            value = object_result_item.get("value")

            self.data[device_code][code] = value

        error_msg = data_response.get("error_msg")

        if error_msg != "Success":
            _LOGGER.error(f"Failed to fetch data, Error: {error_msg}")

    async def _fetch_errors(self, device_code: str):
        if "fault" in self.data:
            self.data.pop("fault")

        data = {"device_code": device_code}

        device_status_response = await self._post_request(GETDEVICESTATUS_PATH, data)
        object_result = device_status_response.get("object_result", {})

        is_fault = object_result.get("is_fault", str(False))

        if bool(is_fault):
            device_fault_response = await self._post_request(GETFAULT_PATH, data)
            object_results = device_fault_response.get("object_result", [])

            if len(object_results) > 0:
                object_result = object_results[0]
                self.data[device_code]["fault"] = object_result.get("description")

    async def _login(self):
        config_data = self._config_manager.data

        username = config_data.get(CONF_USERNAME)
        password = config_data.get(CONF_PASSWORD)

        data = {"user_name": username, "password": password, "type": "2"}

        login_response = await self._post_request(LOGIN_PATH, data)
        object_result = login_response.get("object_result", {})

        for key in object_result:
            self.data[key] = object_result[key]

        self._token = object_result.get("x-token")
        self._headers["x-token"] = self._token

        await self._update_device_code()

    async def _update_device_code(self):
        data = {}

        # Try getting devices without specific product IDs
        device_code_response = await self._post_request(DEVICELIST_PATH)
        object_results = device_code_response.get("object_result", [])

        # Try getting devices with known product IDs
        product_id_data = {'product_ids': PRODUCT_IDS}
        device_code_response_wids = await self._post_request(DEVICELIST_PATH, product_id_data)
        object_results_wids = device_code_response_wids.get("object_result", [])

        # Merge results
        all_object_results = list(set(object_results) + set(object_results_wids))

        for object_result in all_object_results:
            device_code = object_result.get("device_code")

            _LOGGER.debug(f"Discover device: {device_code}, Data: {object_result}")

            data[device_code] = object_result


        self.data = data

        _LOGGER.debug(f"Finished discovering devices, Data: {self.data}")

    async def _post_request(self, endpoint, data: dict | list | None = None) -> dict:
        url = f"{SERVER_URL}{endpoint}"

        async with self._session.post(
            url, headers=self._headers, json=data, ssl=False
        ) as response:
            response.raise_for_status()

            result = await response.json()
            _LOGGER.debug(f"Request to {endpoint}, Result: {result}")

        return result

    @staticmethod
    def _get_request_params(
        device_code: str, protocol_codes: list[str] | dict[str, str]
    ) -> list[dict]:
        if isinstance(protocol_codes, dict):
            result = []
            for protocol_code in protocol_codes:
                value = protocol_codes.get(protocol_code)

                data = {
                    "device_code": device_code,
                    "protocol_code": protocol_code,
                    "value": value,
                }

                result.append(data)
        else:
            result = {
                "device_code": device_code,
                "protocal_codes": protocol_codes,
            }

        return result
