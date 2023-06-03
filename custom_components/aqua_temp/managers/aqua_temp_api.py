"""Platform for climate integration."""
import logging
import sys

from aiohttp import ClientSession

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ..common.consts import (
    ALL_ENTITIES,
    DEVICE_CODE,
    DEVICE_CONTROL_PARAM,
    DEVICE_CONTROL_PROTOCOL_CODE,
    DEVICE_CONTROL_VALUE,
    DEVICE_LISTS,
    DEVICE_REQUEST_PARAMETERS,
    DEVICE_REQUEST_TO_USER,
    FAN_MODE_MAPPING,
    HEADERS,
    HTTP_HEADER_X_TOKEN,
    HVAC_MODE_MAPPING,
    POWER_MODE_OFF,
    POWER_MODE_ON,
    PROTOCAL_CODES,
)
from ..common.endpoints import Endpoints
from ..common.exceptions import LoginError, OperationFailedException
from ..common.protocol_codes import ProtocolCode
from .aqua_temp_config_manager import AquaTempConfigManager

_LOGGER = logging.getLogger(__name__)


class AquaTempAPI:
    data: dict

    _session: ClientSession | None
    _config_manager: AquaTempConfigManager
    _token: str | None
    _user_id: str | None
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
        self._user_id = None

        self._reverse_hvac_mode_mapping = {
            HVAC_MODE_MAPPING[key]: key for key in HVAC_MODE_MAPPING
        }

        self._reverse_fan_mode_mapping = {
            FAN_MODE_MAPPING[key]: key for key in FAN_MODE_MAPPING
        }

    @property
    def is_connected(self):
        result = self._session is not None and self._token is not None

        return result

    async def initialize(self, throw_error: bool = False):
        try:
            if self._session is None:
                if self._hass is None:
                    self._session = ClientSession()
                else:
                    self._session = async_create_clientsession(hass=self._hass)

                await self._connect()

        except LoginError as lex:
            _LOGGER.error("Failed to login, Please update credentials and try again")

            if throw_error:
                raise lex

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(
                f"Failed to initialize session, Error: {ex}, Line: {line_number}"
            )

    async def _connect(self):
        if self._token is None:
            self.protocol_codes.clear()

            await self._login()

            for entity_description in ALL_ENTITIES:
                if (
                    entity_description.key not in self.protocol_codes
                    and entity_description.is_protocol_code
                ):
                    self.protocol_codes.append(entity_description.key)

            await self._load_user_info()
            await self._load_devices()

    async def terminate(self):
        if self._hass is None:
            await self._session.close()

    async def update(self):
        """Fetch new state data for the sensor."""
        try:
            if self.is_connected:
                for device_code in self.data:
                    await self._update_device(device_code)

        except Exception as ex:
            self.set_token()

            await self.initialize()

            _LOGGER.error(f"Error fetching data. Reconnecting, Error: {ex}")

    async def _update_device(self, device_code: str):
        _LOGGER.debug(f"Starting to update device: {device_code}")

        await self._send_passthrough_instruction(device_code)

        await self._fetch_data(device_code)

        await self._fetch_errors(device_code)

    def set_token(self, token: str | None = None):
        self._token = token

        if token is None:
            if HTTP_HEADER_X_TOKEN in self._headers:
                self._headers.pop(HTTP_HEADER_X_TOKEN)
        else:
            self._headers[HTTP_HEADER_X_TOKEN] = token

    async def set_hvac_mode(self, device_code: str, hvac_mode: HVACMode):
        if hvac_mode == HVACMode.OFF:
            await self._set_power_mode(device_code, POWER_MODE_OFF)

        else:
            is_on = self.get_device_power(device_code)

            if not is_on:
                await self._set_power_mode(device_code, POWER_MODE_ON)

                await self._update_device(device_code)

            await self._set_hvac_mode(device_code, hvac_mode)

    async def set_temperature(self, device_code: str, temperature: float):
        """Set new target temperature."""
        hvac_mode = self.get_device_hvac_mode(device_code)
        temp_protocol_code = self.get_target_temperature_protocol_code(hvac_mode)

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: temp_protocol_code,
                    DEVICE_CONTROL_VALUE: temperature,
                },
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: ProtocolCode.SET_TEMP,
                    DEVICE_CONTROL_VALUE: temperature,
                },
            ]
        }

        await self._perform_action(request_data, ProtocolCode.SET_TEMP)

    async def _set_power_mode(self, device_code: str, value):
        """Set new target power mode."""
        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: ProtocolCode.POWER.lower(),
                    DEVICE_CONTROL_VALUE: value,
                }
            ]
        }

        await self._perform_action(request_data, ProtocolCode.POWER)

    async def _set_hvac_mode(self, device_code: str, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            return

        device_mode = HVAC_MODE_MAPPING.get(hvac_mode)

        target_temperature = self.get_device_target_temperature(device_code)

        _LOGGER.info(
            f"Set HVAC Mode: {hvac_mode}, PC Mode: {device_mode}, Target temperature: {target_temperature}"
        )

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: ProtocolCode.MODE,
                    DEVICE_CONTROL_VALUE: device_mode,
                },
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: ProtocolCode.SET_TEMP,
                    DEVICE_CONTROL_VALUE: target_temperature,
                },
            ]
        }

        await self._perform_action(request_data, ProtocolCode.MODE)

    async def set_fan_mode(self, device_code: str, fan_mode):
        """Set new target fan mode."""

        value = FAN_MODE_MAPPING.get(fan_mode)

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: ProtocolCode.MANUAL_MUTE,
                    DEVICE_CONTROL_VALUE: value,
                }
            ]
        }

        await self._perform_action(request_data, ProtocolCode.MANUAL_MUTE)

    async def _perform_action(self, request_data: dict, operation: str):
        operation_response = await self._post_request(
            Endpoints.DEVICE_CONTROL, request_data
        )

        error_msg = operation_response.get("error_msg")

        if error_msg != "Success":
            raise OperationFailedException(operation, request_data, error_msg)

    async def _fetch_data(self, device_code: str):
        data = {
            DEVICE_CODE: device_code,
            PROTOCAL_CODES: self.protocol_codes,
        }

        data_response = await self._post_request(Endpoints.DEVICE_DATA, data)
        object_result_items = data_response.get("object_result", [])

        for object_result_item in object_result_items:
            code = object_result_item.get("code")
            value = object_result_item.get("value")

            self.data[device_code][code] = value

        error_msg = data_response.get("error_msg")

        if error_msg != "Success":
            _LOGGER.error(f"Failed to fetch data, Error: {error_msg}")

    async def _send_passthrough_instruction(self, device_code: str):
        data = {"device_code": device_code, "query_instruction": "630300040001CD89"}

        data_response = await self._post_request(
            Endpoints.DEVICE_PASSTHROUGH_INSTRUCTION, data
        )
        error_msg = data_response.get("error_msg")

        if error_msg != "Success":
            _LOGGER.error(f"Failed to send passthrough instruction, Error: {error_msg}")

    async def _fetch_errors(self, device_code: str):
        if "fault" in self.data:
            self.data.pop("fault")

        data = {"device_code": device_code}

        device_status_response = await self._post_request(Endpoints.DEVICE_STATUS, data)
        object_result = device_status_response.get("object_result", {})

        is_fault = object_result.get("is_fault", str(False))

        if bool(is_fault):
            device_fault_response = await self._post_request(
                Endpoints.DEVICE_FAULT, data
            )
            object_results = device_fault_response.get("object_result", [])

            if len(object_results) > 0:
                object_result = object_results[0]
                self.data[device_code]["fault"] = object_result.get("description")

    async def _login(self):
        config_data = self._config_manager.data

        username = config_data.get(CONF_USERNAME)
        password = config_data.get(CONF_PASSWORD)

        data = {"user_name": username, "password": password, "type": "2"}

        try:
            login_response = await self._post_request(Endpoints.LOGIN, data)
            object_result = login_response.get("object_result", {})

            for key in object_result:
                self.data[key] = object_result[key]

            token = object_result.get(HTTP_HEADER_X_TOKEN)

            self.set_token(token)

        except Exception as ex:
            self.set_token()

            _LOGGER.error(f"Failed to login, Error: {ex}")

        if self._token is None:
            raise LoginError()

    async def _load_user_info(self):
        user_info_response = await self._post_request(Endpoints.USER_INFO)

        object_result = user_info_response.get("object_result", {})
        self._user_id = object_result.get("user_id")

    async def _load_devices(self):
        data = {}
        for device_list_url in DEVICE_LISTS:
            request_data = {}
            request_data_keys = DEVICE_LISTS[device_list_url]

            for request_data_key in request_data_keys:
                if request_data_key == DEVICE_REQUEST_TO_USER:
                    value = self._user_id
                else:
                    value = DEVICE_REQUEST_PARAMETERS.get(request_data_key)

                request_data[request_data_key] = value

            device_code_response = await self._post_request(
                device_list_url, request_data
            )

            object_results = device_code_response.get("object_result", [])

            for object_result in object_results:
                device_code = object_result.get("device_code")

                _LOGGER.debug(
                    f"Discover device: {device_code} by {device_list_url}, Data: {object_result}"
                )

                data[device_code] = object_result

        self.data = data

        _LOGGER.debug(f"Finished discovering devices, Data: {self.data}")

    async def _post_request(
        self, endpoint: Endpoints, data: dict | list | None = None
    ) -> dict | None:
        url = f"{Endpoints.BASE_URL}/{endpoint}"

        async with self._session.post(
            url, headers=self._headers, json=data, ssl=False
        ) as response:
            if endpoint == Endpoints.LOGIN:
                response.raise_for_status()

            if response.ok:
                result = await response.json()
                _LOGGER.debug(f"Request to {endpoint}, Result: {result}")

            else:
                error_message = (
                    f"HTTP request to {endpoint}, "
                    f"Status: {response.status}, "
                    f"Message: {response.reason}"
                )

                result = {"error_msg": error_message}

                _LOGGER.warning(error_message)

        return result

    def get_device_data(self, device_code: str) -> dict | None:
        device_data = self.data.get(device_code)

        return device_data

    def get_device_target_temperature(self, device_code: str) -> float:
        hvac_mode = self.get_device_hvac_mode(device_code)
        target_temperature_protocol_code = self.get_target_temperature_protocol_code(
            hvac_mode
        )

        device_data = self.get_device_data(device_code)
        target_temperature = device_data.get(target_temperature_protocol_code)

        return target_temperature

    def get_device_current_temperature(self, device_code: str) -> float:
        device_data = self.get_device_data(device_code)
        current_temperature = device_data.get(ProtocolCode.CURRENT_TEMPERATURE)

        return current_temperature

    def get_device_hvac_mode(self, device_code: str) -> HVACMode:
        device_data = self.get_device_data(device_code)
        device_mode = device_data.get(ProtocolCode.MODE)
        hvac_mode = self._reverse_hvac_mode_mapping.get(device_mode, HVACMode.OFF)

        return hvac_mode

    def get_device_fan_mode(self, device_code: str) -> str:
        device_data = self.get_device_data(device_code)
        manual_mute = device_data.get(ProtocolCode.MANUAL_MUTE)
        fan_mode = self._reverse_fan_mode_mapping.get(manual_mute)

        return fan_mode

    def get_device_power(self, device_code: str) -> bool:
        device_data = self.get_device_data(device_code)
        power = device_data.get(ProtocolCode.POWER)
        is_on = power == POWER_MODE_ON

        return is_on

    @staticmethod
    def get_target_temperature_protocol_code(hvac_mode: HVACMode):
        hvac_mode_mapping = HVAC_MODE_MAPPING.get(hvac_mode)
        temp_protocol_code = f"R0{hvac_mode_mapping}"

        return temp_protocol_code
