"""Platform for climate integration."""
import logging
import sys

from aiohttp import ClientResponseError, ClientSession

from homeassistant.components.climate.const import HVACMode
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from ..common.consts import (
    CONFIG_HVAC_MAXIMUM,
    CONFIG_HVAC_MINIMUM,
    CONFIG_HVAC_SET,
    CONFIG_HVAC_TARGET,
    CONFIG_SET_CURRENT_TEMPERATURE,
    CONFIG_SET_FAN,
    CONFIG_SET_MODE,
    CONFIG_SET_POWER,
    CONFIG_SET_TEMPERATURE,
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
    POWER_MODE_OFF,
    POWER_MODE_ON,
    PROTOCAL_CODES,
    SIGNAL_AQUA_TEMP_DEVICE_NEW,
)
from ..common.endpoints import Endpoints
from ..common.exceptions import LoginError, OperationFailedException
from .aqua_temp_config_manager import AquaTempConfigManager
from .product_config_manager import ProductConfigurationManager

_LOGGER = logging.getLogger(__name__)


class AquaTempAPI:
    _devices: dict
    _login_details: dict | None

    _session: ClientSession | None
    _config_manager: AquaTempConfigManager
    _token: str | None
    _hass: HomeAssistant | None

    def __init__(
        self,
        hass: HomeAssistant | None,
        config_manager: AquaTempConfigManager,
        product_configuration_manager: ProductConfigurationManager,
    ):
        """Initialize the climate entity."""

        self._devices = {}
        self._login_details = None

        self._session = None
        self._token = None

        self._hass = hass
        self._headers = HEADERS
        self._config_manager = config_manager
        self._product_manager = product_configuration_manager

        self._dispatched_devices = []
        self._device_list_request_data = {}

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
        """Fetch new state parameters for the sensor."""
        try:
            if self._token is None:
                await self._login()
                await self._load_devices()

            for device_code in self._devices:
                await self._update_device(device_code)

        except Exception as ex:
            _LOGGER.error(f"Error fetching parameters, Error: {ex}")

    async def _update_device(self, device_code: str):
        _LOGGER.debug(f"Starting to update device: {device_code}")

        try:
            new_device = device_code not in self._dispatched_devices

            if new_device:
                self._product_manager.set_device(self._devices[device_code])

            await self._send_passthrough_instruction(device_code)

            await self._fetch_data(device_code)

            await self._fetch_errors(device_code)

            if new_device:
                self._dispatched_devices.append(device_code)

                async_dispatcher_send(
                    self._hass,
                    SIGNAL_AQUA_TEMP_DEVICE_NEW,
                    device_code,
                )

        except ClientResponseError as cre:
            error_message = (
                f"Error fetching parameters for device {device_code}, Error: "
            )

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
        target_temperature_pc = self._get_target_temperature_protocol_code(
            device_code, hvac_mode
        )

        set_temp_pc_key = self._product_manager.get_pc_key(
            device_code, CONFIG_SET_TEMPERATURE
        )

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: target_temperature_pc,
                    DEVICE_CONTROL_VALUE: temperature,
                },
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: set_temp_pc_key,
                    DEVICE_CONTROL_VALUE: temperature,
                },
            ]
        }

        await self._perform_action(request_data, set_temp_pc_key)

    async def _set_power_mode(self, device_code: str, value):
        """Set new target power mode."""
        power_pc_key = self._product_manager.get_pc_key(device_code, CONFIG_SET_POWER)

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: power_pc_key.lower(),
                    DEVICE_CONTROL_VALUE: value,
                }
            ]
        }

        await self._perform_action(request_data, power_pc_key)

    async def _set_hvac_mode(self, device_code: str, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            return

        mode_pc_key = self._product_manager.get_pc_key(device_code, CONFIG_SET_MODE)
        set_temp_pc_key = self._product_manager.get_pc_key(
            device_code, CONFIG_SET_TEMPERATURE
        )
        action_pc_key = self._product_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_SET
        )

        target_temperature = self.get_device_target_temperature(device_code)

        _LOGGER.info(
            f"Set HVAC Mode: {hvac_mode}, PC Mode: {action_pc_key}, Target temperature: {target_temperature}"
        )

        control_params = []

        set_target_temp = {
            DEVICE_CODE: device_code,
            DEVICE_CONTROL_PROTOCOL_CODE: set_temp_pc_key,
            DEVICE_CONTROL_VALUE: target_temperature,
        }

        control_params.append(set_target_temp)

        if mode_pc_key != set_temp_pc_key:
            set_mode = {
                DEVICE_CODE: device_code,
                DEVICE_CONTROL_PROTOCOL_CODE: mode_pc_key,
                DEVICE_CONTROL_VALUE: action_pc_key,
            }

            control_params.append(set_mode)

        request_data = {
            DEVICE_CONTROL_PARAM: control_params
        }

        await self._perform_action(request_data, mode_pc_key)

    async def set_fan_mode(self, device_code: str, fan_mode):
        """Set new target fan mode."""
        fan_pc_key = self._product_manager.get_pc_key(device_code, CONFIG_SET_FAN)

        value = FAN_MODE_MAPPING.get(fan_mode)

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    DEVICE_CODE: device_code,
                    DEVICE_CONTROL_PROTOCOL_CODE: fan_pc_key,
                    DEVICE_CONTROL_VALUE: value,
                }
            ]
        }

        await self._perform_action(request_data, fan_pc_key)

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
        codes = self._product_manager.get_supported_protocol_codes(device_code)

        data = {
            DEVICE_CODE: device_code,
            PROTOCAL_CODES: codes,
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
            _LOGGER.error(f"Failed to fetch parameters, Error: {error_msg}")

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

                _LOGGER.debug(
                    f"Discover device: {device_code} by {device_list_url}, Data: {device}"
                )

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
        target_temperature_pc = self._get_target_temperature_protocol_code(
            device_code, hvac_mode
        )

        device_data = self.get_device_data(device_code)
        target_temperature = device_data.get(target_temperature_pc)

        if target_temperature == "":
            target_temperature = None

        if target_temperature is not None:
            target_temperature = float(str(target_temperature))

        return target_temperature

    def get_device_current_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code)
        pc_key = self._product_manager.get_pc_key(
            device_code, CONFIG_SET_CURRENT_TEMPERATURE
        )
        current_temperature = device_data.get(pc_key)

        if current_temperature == "":
            current_temperature = None

        if current_temperature is not None:
            current_temperature = float(str(current_temperature))

        return current_temperature

    def get_device_minimum_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code)

        hvac_mode = self.get_device_hvac_mode(device_code)
        key = self._product_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_MINIMUM
        )

        temperature = device_data.get(key)

        if temperature == "":
            temperature = None

        if temperature is not None:
            temperature = float(str(temperature))

        return temperature

    def get_device_maximum_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code)

        hvac_mode = self.get_device_hvac_mode(device_code)

        key = self._product_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_MAXIMUM
        )

        temperature = device_data.get(key)

        if temperature == "":
            temperature = None

        if temperature is not None:
            temperature = float(str(temperature))

        return temperature

    def get_device_hvac_mode(self, device_code: str) -> HVACMode:
        device_data = self.get_device_data(device_code)
        pc_key = self._product_manager.get_pc_key(device_code, CONFIG_SET_MODE)
        device_mode = device_data.get(pc_key)

        hvac_mode = self._product_manager.get_hvac_reverse_mapping(
            device_code, device_mode
        )
        result = HVACMode(hvac_mode)

        return result

    def get_device_fan_mode(self, device_code: str) -> str:
        device_data = self.get_device_data(device_code)
        pc_key = self._product_manager.get_pc_key(device_code, CONFIG_SET_FAN)
        manual_mute = device_data.get(pc_key)

        fan_mode = self._product_manager.get_fan_reverse_mapping(
            device_code, manual_mute
        )

        return fan_mode

    def get_device_power(self, device_code: str) -> bool:
        device_data = self.get_device_data(device_code)
        pc_key = self._product_manager.get_pc_key(device_code, CONFIG_SET_POWER)

        power = device_data.get(pc_key)
        is_on = power == POWER_MODE_ON

        return is_on

    def _get_target_temperature_protocol_code(
        self, device_code: str, hvac_mode: HVACMode
    ):
        target_temperature_pc = self._product_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_TARGET
        )

        _LOGGER.debug(f"Target temp PC {target_temperature_pc}, HA Mode: {hvac_mode}")

        return target_temperature_pc
