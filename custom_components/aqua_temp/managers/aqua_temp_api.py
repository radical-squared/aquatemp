"""Platform for climate integration."""
from copy import copy
import logging
import sys

from aiohttp import ClientResponseError, ClientSession

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from ..common.consts import (
    DEVICE_CODE,
    DEVICE_CONTROL_PARAM,
    DEVICE_CONTROL_PROTOCOL_CODE,
    DEVICE_CONTROL_VALUE,
    DEVICE_LISTS,
    DEVICE_PRODUCT_ID,
    DEVICE_REQUEST_PARAMETERS,
    DEVICE_REQUEST_TO_USER,
    FAN_MODE_MAPPING,
    HEADERS,
    HTTP_HEADER_X_TOKEN,
    POWER_MODE_OFF,
    POWER_MODE_ON,
    PROTOCAL_CODES,
    SIGNAL_AQUA_TEMP_DEVICE_NEW,
)
from ..common.endpoints import Endpoints
from ..common.entity_descriptions import ALL_ENTITIES
from ..common.exceptions import LoginError, OperationFailedException
from ..common.hvac_mode_mapping import (
    HVAC_MODE_MAPPING,
    HVAC_MODE_MAXIMUM_TEMPERATURE,
    HVAC_MODE_MINIMUM_TEMPERATURE,
    HVAC_MODE_TARGET_TEMPERATURE,
)
from ..common.protocol_codes import PROTOCOL_CODE_OVERRIDES, ProtocolCode
from .aqua_temp_config_manager import AquaTempConfigManager

_LOGGER = logging.getLogger(__name__)


class AquaTempAPI:
    _devices: dict
    _login_details: dict | None

    _session: ClientSession | None
    _config_manager: AquaTempConfigManager
    _token: str | None
    _hass: HomeAssistant | None

    def __init__(
        self, hass: HomeAssistant | None, config_manager: AquaTempConfigManager
    ):
        """Initialize the climate entity."""

        self._devices = {}
        self._login_details = None

        self._session = None
        self._token = None

        self._hass = hass
        self._headers = HEADERS
        self._config_manager = config_manager
        self._dispatched_devices = []
        self._device_list_request_data = {}

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

    @property
    def login_details(self):
        result = self._login_details

        return result

    @property
    def devices(self):
        result = self._devices

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
            await self._login()

            await self._load_devices()

    async def terminate(self):
        if self._hass is None:
            await self._session.close()

    async def update(self):
        """Fetch new state data for the sensor."""
        try:
            if self._token is None:
                await self._login()
                await self._load_devices()

            for device_code in self._devices:
                await self._update_device(device_code)

        except Exception as ex:
            _LOGGER.error(f"Error fetching data, Error: {ex}")

    async def _update_device(self, device_code: str):
        _LOGGER.debug(f"Starting to update device: {device_code}")

        try:
            await self._send_passthrough_instruction(device_code)

            await self._fetch_data(device_code)

            await self._fetch_errors(device_code)

            if device_code not in self._dispatched_devices:
                self._dispatched_devices.append(device_code)

                async_dispatcher_send(
                    self._hass,
                    SIGNAL_AQUA_TEMP_DEVICE_NEW,
                    device_code,
                )

        except ClientResponseError as cre:
            error_message = f"Error fetching data for device {device_code}, Error: "

            if cre.status == 401:
                _LOGGER.warning(f"{error_message}expired token")

                self.set_token()

            else:
                _LOGGER.error(f"{error_message}{cre}")

    def set_token(self, token: str | None = None):
        self._device_list_request_data = {}
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
        try:
            operation_response = await self._post_request(
                Endpoints.DEVICE_CONTROL, request_data
            )

            error_msg = operation_response.get("error_msg")

            if error_msg != "Success":
                raise OperationFailedException(operation, request_data, error_msg)

        except ClientResponseError as cre:
            if cre.status == 401:
                self.set_token()

            raise cre

    async def _fetch_data(self, device_code: str):
        device_data = self.get_device_data(device_code)
        device_protocal_codes = device_data.get(PROTOCAL_CODES)

        protocal_codes = [
            device_protocal_code.key for device_protocal_code in device_protocal_codes
        ]

        data = {
            DEVICE_CODE: device_code,
            PROTOCAL_CODES: protocal_codes,
        }

        data_response = await self._post_request(Endpoints.DEVICE_DATA, data)
        object_result_items = data_response.get("object_result", [])

        for object_result_item in object_result_items:
            code = object_result_item.get("code")
            value = object_result_item.get("value")

            if value is not None and isinstance(value, str) and value == "":
                value = None

            self._devices[device_code][code] = value

        error_msg = data_response.get("error_msg")

        if error_msg != "Success":
            _LOGGER.error(f"Failed to fetch data, Error: {error_msg}")

    async def _send_passthrough_instruction(self, device_code: str):
        data = {DEVICE_CODE: device_code, "query_instruction": "630300040001CD89"}

        data_response = await self._post_request(
            Endpoints.DEVICE_PASSTHROUGH_INSTRUCTION, data
        )
        error_msg = data_response.get("error_msg")

        if error_msg != "Success":
            _LOGGER.error(f"Failed to send passthrough instruction, Error: {error_msg}")

    async def _fetch_errors(self, device_code: str):
        data = {DEVICE_CODE: device_code}

        device_status_response = await self._post_request(Endpoints.DEVICE_STATUS, data)
        object_result = device_status_response.get("object_result", {})

        is_fault = object_result.get("is_fault", str(False))
        fault_description = None

        if bool(is_fault):
            device_fault_response = await self._post_request(
                Endpoints.DEVICE_FAULT, data
            )
            object_results = device_fault_response.get("object_result", [])

            if len(object_results) > 0:
                object_result = object_results[0]
                fault_description = object_result.get("description")

        device_data = self._devices[device_code]

        if fault_description is None:
            if "fault" in device_data:
                device_data.pop("fault")
        else:
            device_data["fault"] = fault_description

    async def _login(self):
        config_data = self._config_manager.data

        username = config_data.get(CONF_USERNAME)
        password = config_data.get(CONF_PASSWORD)

        data = {"user_name": username, "password": password, "type": "2"}

        try:
            login_response = await self._post_request(Endpoints.LOGIN, data)
            object_result = login_response.get("object_result", {})

            self._login_details = object_result

            token = object_result.get(HTTP_HEADER_X_TOKEN)

            self.set_token(token)

            await self._load_user_info()

        except Exception as ex:
            self.set_token()

            _LOGGER.error(f"Failed to login, Error: {ex}")

        if self._token is None:
            raise LoginError()

    async def _load_user_info(self):
        user_info_response = await self._post_request(Endpoints.USER_INFO)

        object_result = user_info_response.get("object_result", {})
        user_id = object_result.get("user_id")

        for device_list_url in DEVICE_LISTS:
            request_data = {}
            request_data_keys = DEVICE_LISTS[device_list_url]

            for request_data_key in request_data_keys:
                if request_data_key == DEVICE_REQUEST_TO_USER:
                    value = user_id
                else:
                    value = DEVICE_REQUEST_PARAMETERS.get(request_data_key)

                request_data[request_data_key] = value

            self._device_list_request_data[device_list_url] = request_data

    async def _load_devices(self):
        for device_list_url in DEVICE_LISTS:
            request_data = self._device_list_request_data[device_list_url]

            device_code_response = await self._post_request(
                device_list_url, request_data
            )

            devices = device_code_response.get("object_result", [])

            for device in devices:
                device_code = device.get(DEVICE_CODE)
                device_product_id = device.get(DEVICE_PRODUCT_ID)

                _LOGGER.debug(
                    f"Discover device: {device_code} by {device_list_url}, Data: {device}"
                )

                protocol_code_overrides = PROTOCOL_CODE_OVERRIDES.get(device_product_id)
                device_entities = copy(
                    [entity for entity in ALL_ENTITIES if entity.is_protocol_code]
                )

                for entity in device_entities:
                    if protocol_code_overrides is not None:
                        for replace_key in protocol_code_overrides:
                            replace_with = protocol_code_overrides[replace_key]
                            key = entity.key.replace(replace_key, replace_with)

                            entity.key = key

                device[PROTOCAL_CODES] = device_entities

                self._devices[device_code] = device

                _LOGGER.info(f"Discovering device {device_code}")

    async def _post_request(
        self, endpoint: Endpoints, data: dict | list | None = None
    ) -> dict | None:
        url = f"{Endpoints.BASE_URL}/{endpoint}"

        if endpoint == Endpoints.DEVICE_CONTROL:
            _LOGGER.info(f"Sending request to control device, Data: {data}")

        async with self._session.post(
            url, headers=self._headers, json=data, ssl=False
        ) as response:
            response.raise_for_status()

            result = await response.json()
            _LOGGER.debug(f"Request to {endpoint}, Result: {result}")

        return result

    def get_device_data(self, device_code: str) -> dict | None:
        device_data = self._devices.get(device_code)

        return device_data

    def get_device_target_temperature(self, device_code: str) -> float | None:
        hvac_mode = self.get_device_hvac_mode(device_code)
        target_temperature_protocol_code = self.get_target_temperature_protocol_code(
            hvac_mode
        )

        device_data = self.get_device_data(device_code)
        target_temperature = device_data.get(target_temperature_protocol_code)

        if target_temperature == "":
            target_temperature = None

        if target_temperature is not None:
            target_temperature = float(str(target_temperature))

        return target_temperature

    def get_device_current_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code)
        current_temperature = device_data.get(ProtocolCode.CURRENT_TEMPERATURE)

        if current_temperature == "":
            current_temperature = None

        if current_temperature is not None:
            current_temperature = float(str(current_temperature))

        return current_temperature

    def get_device_minimum_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code)

        hvac_mode = self.get_device_hvac_mode(device_code)
        key = HVAC_MODE_MINIMUM_TEMPERATURE.get(hvac_mode)

        temperature = device_data.get(key)

        if temperature == "":
            temperature = None

        if temperature is not None:
            temperature = float(str(temperature))

        return temperature

    def get_device_maximum_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code)

        hvac_mode = self.get_device_hvac_mode(device_code)
        key = HVAC_MODE_MAXIMUM_TEMPERATURE.get(hvac_mode)

        temperature = device_data.get(key)

        if temperature == "":
            temperature = None

        if temperature is not None:
            temperature = float(str(temperature))

        return temperature

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
        target_temperature_protocol_code = HVAC_MODE_TARGET_TEMPERATURE.get(hvac_mode)

        _LOGGER.debug(
            f"Target temp PC {target_temperature_protocol_code}, HA Mode: {hvac_mode}"
        )

        return target_temperature_protocol_code
