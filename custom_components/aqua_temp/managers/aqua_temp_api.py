"""Platform for climate integration."""
from asyncio import sleep
from copy import copy
import hashlib
import json
import logging
import sys
import unicodedata

from aiohttp import ClientResponseError, ClientSession

from custom_components.aqua_temp.models.exceptions import (
    InvalidTokenError,
    LoginError,
    OperationFailedException,
)
from homeassistant.components.climate.const import HVACMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from ..common.api_types import DEVICE_LISTS, DEVICE_REQUEST_PARAMETERS, APIParam
from ..common.consts import (
    API_MAX_ATTEMPTS,
    CONFIG_HVAC_MAXIMUM,
    CONFIG_HVAC_MINIMUM,
    CONFIG_HVAC_SET,
    CONFIG_HVAC_TARGET,
    CONFIG_SET_CURRENT_TEMPERATURE,
    CONFIG_SET_FAN,
    CONFIG_SET_MODE,
    CONFIG_SET_POWER,
    CONFIG_SET_TEMPERATURE,
    DEVICE_CONTROL_PARAM,
    DEVICE_CONTROL_VALUE,
    FAN_MODE_MAPPING,
    HEADERS,
    HTTP_HEADER_X_TOKEN,
    POWER_MODE_OFF,
    POWER_MODE_ON,
    SIGNAL_AQUA_TEMP_DEVICE_NEW,
)
from ..common.endpoints import Endpoints
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
        _LOGGER.debug(f"Initializing API, Throw Error: {throw_error}")

        if self._session is None:
            if self._hass is None:
                self._session = ClientSession()
            else:
                self._session = async_create_clientsession(hass=self._hass)

        try:
            await self._connect()

        except LoginError:
            if throw_error:
                raise
            _LOGGER.error("Failed to login, Please update credentials and try again")

        except Exception:
            if throw_error:
                raise
            _LOGGER.warning("Failed to initialize session", exc_info=True)

    async def _connect(self):
        if self._token is None:
            _LOGGER.debug("No token available, Login AquaTemp API and fetching devices")
            await self._login()

            await self._load_devices()

    async def terminate(self):
        if self._hass is None:
            await self._session.close()

    async def update(self):
        """Fetch new state parameters for the sensor."""
        await self._internal_update()

    async def _internal_update(self):
        """Fetch new state with up to API_MAX_ATTEMPTS retries.

        Always clears the token between failed attempts so the next try goes
        through a full re-login, re-loads user info, and re-loads devices.
        Without that, a partial failure (e.g. network error after _login set
        the token but before _load_user_info populated _device_list_request_data)
        would leave _devices empty and self._token set; subsequent ticks would
        iterate an empty for-loop, raise no error, and silently report success
        forever — a "stuck token" state.

        AquaTemp's cloud only allows one active session per credential, so if
        another client (phone app, second HA) is also logging in with the same
        account we'll fight an unwinnable war. The README workaround is to use
        a second account and share the device to it.
        """
        last_error: Exception | None = None
        last_line: int | None = None

        for attempt in range(1, API_MAX_ATTEMPTS + 1):
            try:
                await self._connect()

                for device_code in self._devices:
                    await self._update_device(device_code)

                return

            except Exception as ex:
                _, _, tb = sys.exc_info()
                last_line = tb.tb_lineno if tb is not None else None
                last_error = ex
                self.set_token()

            if attempt < API_MAX_ATTEMPTS:
                await sleep(1)

        _LOGGER.error(
            f"Failed to update after {API_MAX_ATTEMPTS} attempts, "
            f"Error: {last_error}, Line: {last_line}"
        )
        raise last_error

    async def _update_device(self, device_code: str):
        _LOGGER.debug(f"Starting to update device: {device_code}")

        try:
            new_device = device_code not in self._dispatched_devices

            if new_device:
                device = self.get_device_data(device_code)
                product_id = self._get_device_product_id(device)

                self._config_manager.set_device(device_code, product_id)

            param_keep_alive = self._config_manager.get_api_param(APIParam.KeepAlive)

            if param_keep_alive:
                await self._send_passthrough_instruction(device_code)

            await self._fetch_data(device_code)

            await self._fetch_errors(device_code)

            if new_device:
                self._dispatched_devices.append(device_code)

                async_dispatcher_send(
                    self._hass,
                    SIGNAL_AQUA_TEMP_DEVICE_NEW,
                    self._config_manager.entry_id,
                    device_code,
                )

        except ClientResponseError as cre:
            if cre.status == 401:
                raise InvalidTokenError(f"Update device: {device_code}")

            else:
                raise cre

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

        set_temp_pc_key = self._config_manager.get_pc_key(
            device_code, CONFIG_SET_TEMPERATURE
        )

        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)
        param_protocol_code = self._config_manager.get_api_param(APIParam.ProtocolCode)

        pcs_to_update = []
        for pc in [target_temperature_pc, set_temp_pc_key]:
            if pc and pc not in pcs_to_update:
                pcs_to_update.append(pc)

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    param_device_code: device_code,
                    param_protocol_code: pc,
                    DEVICE_CONTROL_VALUE: temperature,
                }
                for pc in pcs_to_update
            ]
        }

        op_name = target_temperature_pc or set_temp_pc_key or "Set_Temp"
        await self._perform_action(request_data, op_name)

        if device_code in self._devices:
            for pc in pcs_to_update:
                self._devices[device_code][pc] = str(temperature)

    async def _set_power_mode(self, device_code: str, value):
        """Set new target power mode."""
        power_pc_key = self._config_manager.get_pc_key(device_code, CONFIG_SET_POWER)

        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)
        param_protocol_code = self._config_manager.get_api_param(APIParam.ProtocolCode)

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    param_device_code: device_code,
                    param_protocol_code: power_pc_key,
                    DEVICE_CONTROL_VALUE: value,
                }
            ]
        }

        await self._perform_action(request_data, power_pc_key)

        if device_code in self._devices:
            self._devices[device_code][power_pc_key] = str(value)

    async def set_power(self, device_code: str, is_on: bool):
        """Set device power state directly."""
        power_mode = POWER_MODE_ON if is_on else POWER_MODE_OFF
        await self._set_power_mode(device_code, power_mode)

    async def set_operation_mode(self, device_code: str, operation_value: str):
        """Set device operation mode directly (e.g. for water heater)."""
        mode_pc_key = (
            self._config_manager.get_pc_key(device_code, CONFIG_SET_MODE)
            or "Mode"
        )
        set_temp_pc_key = (
            self._config_manager.get_pc_key(device_code, CONFIG_SET_TEMPERATURE)
            or "R01"
        )
        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)
        param_protocol_code = self._config_manager.get_api_param(APIParam.ProtocolCode)

        is_on = self.get_device_power(device_code)

        target_temperature = self.get_device_target_temperature(device_code)
        if target_temperature is None:
            device_data = self.get_device_data(device_code) or {}
            raw_temp = (
                device_data.get(set_temp_pc_key)
                or device_data.get("R01")
                or device_data.get("Set_Temp")
            )
            if raw_temp not in (None, ""):
                try:
                    target_temperature = float(str(raw_temp))
                except (ValueError, TypeError):
                    target_temperature = 50.0
            else:
                target_temperature = 50.0

        control_params = []

        if not is_on:
            power_pc_key = (
                self._config_manager.get_pc_key(device_code, CONFIG_SET_POWER)
                or "Power"
            )
            control_params.append({
                param_device_code: device_code,
                param_protocol_code: power_pc_key,
                DEVICE_CONTROL_VALUE: POWER_MODE_ON,
            })

        if set_temp_pc_key and target_temperature is not None:
            control_params.append({
                param_device_code: device_code,
                param_protocol_code: set_temp_pc_key,
                DEVICE_CONTROL_VALUE: target_temperature,
            })

        control_params.append({
            param_device_code: device_code,
            param_protocol_code: mode_pc_key,
            DEVICE_CONTROL_VALUE: str(operation_value),
        })

        request_data = {DEVICE_CONTROL_PARAM: control_params}
        await self._perform_action(request_data, mode_pc_key)

        if device_code in self._devices:
            self._devices[device_code][mode_pc_key] = str(operation_value)
            if not is_on:
                power_pc_key = (
                    self._config_manager.get_pc_key(device_code, CONFIG_SET_POWER)
                    or "Power"
                )
                self._devices[device_code][power_pc_key] = POWER_MODE_ON

    async def _set_hvac_mode(self, device_code: str, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            return

        mode_pc_key = self._config_manager.get_pc_key(device_code, CONFIG_SET_MODE)
        set_temp_pc_key = self._config_manager.get_pc_key(
            device_code, CONFIG_SET_TEMPERATURE
        )
        action_pc_key = self._config_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_SET
        )

        target_temperature = self.get_device_target_temperature(device_code)

        _LOGGER.info(
            f"Set HVAC Mode: {hvac_mode}, PC Mode: {action_pc_key}, Target temperature: {target_temperature}"
        )

        control_params = []

        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)
        param_protocol_code = self._config_manager.get_api_param(APIParam.ProtocolCode)

        set_target_temp = {
            param_device_code: device_code,
            param_protocol_code: set_temp_pc_key,
            DEVICE_CONTROL_VALUE: target_temperature,
        }

        control_params.append(set_target_temp)

        if mode_pc_key != set_temp_pc_key:
            set_mode = {
                param_device_code: device_code,
                param_protocol_code: mode_pc_key,
                DEVICE_CONTROL_VALUE: action_pc_key,
            }

            control_params.append(set_mode)

        request_data = {DEVICE_CONTROL_PARAM: control_params}

        await self._perform_action(request_data, mode_pc_key)

    async def set_fan_mode(self, device_code: str, fan_mode):
        """Set new target fan mode."""
        fan_pc_key = self._config_manager.get_pc_key(device_code, CONFIG_SET_FAN)

        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)
        param_protocol_code = self._config_manager.get_api_param(APIParam.ProtocolCode)

        value = FAN_MODE_MAPPING.get(fan_mode)

        request_data = {
            DEVICE_CONTROL_PARAM: [
                {
                    param_device_code: device_code,
                    param_protocol_code: fan_pc_key,
                    DEVICE_CONTROL_VALUE: value,
                }
            ]
        }

        await self._perform_action(request_data, fan_pc_key)

    async def _perform_action(
        self, request_data: dict, operation: str, attempt: int = 1
    ):
        error = None

        try:
            param_error_msg = self._config_manager.get_api_param(APIParam.ErrorMessage)
            param_error_code = self._config_manager.get_api_param(APIParam.ErrorCode)

            operation_response = await self._post_request(
                Endpoints.DeviceControl, request_data
            )

            error_msg = operation_response.get(param_error_msg)

            if error_msg != "Success":
                error_code = operation_response.get(param_error_code)
                if error_code == "-100":
                    self.set_token()

                    error = InvalidTokenError(
                        f"Perform operation {operation}, "
                        f"Data: {json.dumps(request_data)}, "
                        f"Attempt: {attempt}"
                    )

                else:
                    _LOGGER.error(
                        f"DeviceControl failed for {operation}, "
                        f"Code: {error_code}, Msg: {error_msg}, "
                        f"Request: {request_data}"
                    )
                    error = OperationFailedException(
                        operation, request_data, f"{error_code}: {error_msg}"
                    )

        except Exception as ex:
            error = ex

        if error is not None:
            if attempt < API_MAX_ATTEMPTS:
                await sleep(1)

                await self._connect()

                await self._perform_action(request_data, operation, attempt + 1)

            else:
                raise error

    async def _fetch_data(self, device_code: str):
        codes = self._config_manager.get_supported_protocol_codes(device_code)

        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)
        param_protocal_codes = self._config_manager.get_api_param(
            APIParam.ProtocalCodes
        )
        param_object_result = self._config_manager.get_api_param(APIParam.ObjectResult)
        param_error_msg = self._config_manager.get_api_param(APIParam.ErrorMessage)
        param_error_code = self._config_manager.get_api_param(APIParam.ErrorCode)

        data = {
            param_device_code: device_code,
            param_protocal_codes: codes,
        }

        data_response = await self._post_request(Endpoints.DeviceData, data)
        error_msg = data_response.get(param_error_msg)

        object_result_items = data_response.get(param_object_result, [])

        if error_msg == "Success":
            for object_result_item in object_result_items:
                code = object_result_item.get("code")
                value = object_result_item.get("value")

                if value is not None and isinstance(value, str) and value == "":
                    value = None

                self._devices[device_code][code] = value

        else:
            error_code = data_response.get(param_error_code)
            if error_code == "-100":
                raise InvalidTokenError(f"Fetch data for device {device_code}")

            else:
                _LOGGER.error(f"Failed to fetch parameters, Error: {error_msg}")

    async def _send_passthrough_instruction(self, device_code: str):
        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)

        data = {param_device_code: device_code, "query_instruction": "630300040001CD89"}

        data_response = await self._post_request(
            Endpoints.DevicePassthroughInstruction, data
        )
        error_msg = data_response.get("error_msg")

        if error_msg != "Success":
            _LOGGER.error(f"Failed to send passthrough instruction, Error: {error_msg}")

    async def _fetch_errors(self, device_code: str):
        param_device_code = self._config_manager.get_api_param(APIParam.DeviceCode)
        param_object_result = self._config_manager.get_api_param(APIParam.ObjectResult)
        param_is_fault = self._config_manager.get_api_param(APIParam.IsFault)

        data = {param_device_code: device_code}

        device_status_response = await self._post_request(Endpoints.DeviceStatus, data)
        object_result = device_status_response.get(param_object_result, {})

        is_fault = object_result.get(param_is_fault, str(False))
        fault_description = None

        if bool(is_fault):
            device_fault_response = await self._post_request(
                Endpoints.DeviceFault, data
            )
            object_results = device_fault_response.get(param_object_result, [])

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
        param_username = self._config_manager.get_api_param(APIParam.Username)
        param_object_result = self._config_manager.get_api_param(APIParam.ObjectResult)

        config_data = self._config_manager.config_data

        password_hashed = hashlib.md5(
            config_data.password.encode("utf-8")
        ).hexdigest()

        data = {param_username: config_data.username, "password": password_hashed}

        login_response = await self._post_request(Endpoints.Login, data)
        object_result = login_response.get(param_object_result, {})

        self._login_details = object_result

        token = object_result.get(HTTP_HEADER_X_TOKEN)

        if token is None:
            _LOGGER.warning(
                "Login failed (no x-token in response). "
                "error_code=%s, error_msg=%s, error_msg_code=%s",
                login_response.get("error_code"),
                login_response.get("error_msg"),
                login_response.get("error_msg_code"),
            )
            # Shape-only diagnostics (no credential content), at DEBUG.
            # If chars != utf8_bytes the password has multibyte unicode; if
            # nfc_utf8_bytes differs again the input was non-NFC-normalized;
            # leading/trailing_ws and all_printable catch hidden whitespace
            # and zero-width chars from copy-paste.
            pw = config_data.password
            un = config_data.username
            _LOGGER.debug(
                "Login failure diagnostics (shape only): "
                "password chars=%d, utf8_bytes=%d, nfc_utf8_bytes=%d, "
                "leading_ws=%s, trailing_ws=%s, all_printable=%s, all_ascii=%s; "
                "username chars=%d, utf8_bytes=%d, has_plus=%s, has_uppercase=%s",
                len(pw),
                len(pw.encode("utf-8")),
                len(unicodedata.normalize("NFC", pw).encode("utf-8")),
                pw != pw.lstrip(),
                pw != pw.rstrip(),
                all(c.isprintable() for c in pw),
                pw.isascii(),
                len(un),
                len(un.encode("utf-8")),
                "+" in un,
                un != un.lower(),
            )
            self.set_token()
            raise LoginError()

        self.set_token(token)
        await self._load_user_info()

    async def _load_user_info(self):
        param_object_result = self._config_manager.get_api_param(APIParam.ObjectResult)
        param_user_id = self._config_manager.get_api_param(APIParam.UserId)

        user_info_response = await self._post_request(Endpoints.UserInfo)

        object_result = user_info_response.get(param_object_result, {})
        user_id = object_result.get(param_user_id)

        for device_list_url in DEVICE_LISTS:
            request_data = {}
            request_data_keys = DEVICE_LISTS[device_list_url]

            for request_data_key in request_data_keys:
                if request_data_key == APIParam.ToUser:
                    value = user_id

                else:
                    value = DEVICE_REQUEST_PARAMETERS.get(request_data_key)

                request_data_param = self._config_manager.get_api_param(
                    request_data_key
                )

                request_data[request_data_param] = value

            self._device_list_request_data[device_list_url] = request_data

    async def _load_devices(self):
        param_object_result = self._config_manager.get_api_param(APIParam.ObjectResult)

        for device_list_url in DEVICE_LISTS:
            request_data = self._device_list_request_data[device_list_url]

            device_code_response = await self._post_request(
                device_list_url, request_data
            )

            devices = device_code_response.get(param_object_result, [])

            for device in devices:
                device_code = self._get_device_id(device)

                _LOGGER.debug(
                    f"Discover device: {device_code} by {device_list_url}, Data: {device}"
                )

                self._devices[device_code] = device

                _LOGGER.info(f"Discovering device {device_code}")

        if not self._devices:
            await self._load_devices_unfiltered(param_object_result)

    async def _load_devices_unfiltered(self, param_object_result):
        param_product_ids = self._config_manager.get_api_param(APIParam.ProductIds)

        _LOGGER.warning(
            "No devices matched the PRODUCT_IDS allow-list — retrying device discovery without productIds filter"
        )

        for device_list_url in DEVICE_LISTS:
            request_data = {
                k: v
                for k, v in self._device_list_request_data[device_list_url].items()
                if k != param_product_ids
            }

            try:
                device_code_response = await self._post_request(
                    device_list_url, request_data
                )
            except Exception as ex:
                _LOGGER.debug(
                    f"Unfiltered discovery to {device_list_url} failed: {ex}"
                )
                continue

            devices = device_code_response.get(param_object_result, [])

            for device in devices:
                device_code = self._get_device_id(device)
                product_id = self._get_device_product_id(device)

                _LOGGER.warning(
                    f"Unfiltered discovery: device {device_code} productId={product_id} (not in PRODUCT_IDS allow-list)"
                )
                _LOGGER.debug(
                    f"Discover device: {device_code} by {device_list_url}, Data: {device}"
                )

                self._devices[device_code] = device

    async def _post_request(
        self, endpoint: Endpoints, data: dict | list | None = None
    ) -> dict | None:
        param_url = self._config_manager.get_api_param(APIParam.URL)
        param_suffix = self._config_manager.get_api_param(APIParam.Suffix)

        url = f"{param_url}/{endpoint}{param_suffix}"

        if endpoint == Endpoints.DeviceControl:
            _LOGGER.info(f"Sending request to control device, Data: {data}")

        async with self._session.post(
            url, headers=self._headers, json=data, ssl=False
        ) as response:
            response.raise_for_status()

            result = await response.json()
            _LOGGER.debug(f"Request to {url}, Body: {data}, Result: {result}")

        return result

    def get_device_data(self, device_code: str) -> dict | None:
        device_data = copy(self._devices.get(device_code))

        return device_data

    def get_device_target_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code) or {}
        hvac_mode = self.get_device_hvac_mode(device_code)
        target_temperature_pc = self._get_target_temperature_protocol_code(
            device_code, hvac_mode
        )

        target_temperature = (
            device_data.get(target_temperature_pc) if target_temperature_pc else None
        )

        if target_temperature in ("", None):
            set_temp_pc = self._config_manager.get_pc_key(
                device_code, CONFIG_SET_TEMPERATURE
            )
            if set_temp_pc:
                target_temperature = device_data.get(set_temp_pc)

        if target_temperature in ("", None):
            for fallback_code in ["R01", "Set_Temp"]:
                val = device_data.get(fallback_code)
                if val not in ("", None):
                    target_temperature = val
                    break

        if target_temperature not in ("", None):
            try:
                target_temperature = float(str(target_temperature))
            except (ValueError, TypeError):
                target_temperature = None

        return target_temperature

    def get_device_current_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code) or {}
        pc_key = self._config_manager.get_pc_key(
            device_code, CONFIG_SET_CURRENT_TEMPERATURE
        )
        current_temperature = device_data.get(pc_key) if pc_key else None

        if current_temperature in ("", None):
            for fallback_code in ["T10", "T02"]:
                val = device_data.get(fallback_code)
                if val not in ("", None):
                    current_temperature = val
                    break

        if current_temperature not in ("", None):
            try:
                current_temperature = float(str(current_temperature))
            except (ValueError, TypeError):
                current_temperature = None

        return current_temperature

    def get_device_minimum_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code) or {}
        hvac_mode = self.get_device_hvac_mode(device_code)
        key = self._config_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_MINIMUM
        )

        temperature = None
        if key is not None and key in device_data:
            temperature = device_data.get(key)
        elif key is not None and (
            isinstance(key, (int, float))
            or (isinstance(key, str) and key.replace(".", "", 1).isdigit())
        ):
            temperature = key

        if temperature in ("", None):
            temperature = 30.0

        try:
            return float(str(temperature))
        except (ValueError, TypeError):
            return 30.0

    def get_device_maximum_temperature(self, device_code: str) -> float | None:
        device_data = self.get_device_data(device_code) or {}
        hvac_mode = self.get_device_hvac_mode(device_code)
        key = self._config_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_MAXIMUM
        )

        temperature = None
        if key is not None and key in device_data:
            temperature = device_data.get(key)
        elif key is not None and (
            isinstance(key, (int, float))
            or (isinstance(key, str) and key.replace(".", "", 1).isdigit())
        ):
            temperature = key

        if temperature in ("", None):
            temperature = 65.0

        try:
            return float(str(temperature))
        except (ValueError, TypeError):
            return 65.0

    def get_device_hvac_mode(self, device_code: str) -> HVACMode:
        device_data = self.get_device_data(device_code)
        pc_key = self._config_manager.get_pc_key(device_code, CONFIG_SET_MODE)
        device_mode = device_data.get(pc_key)

        hvac_mode = self._config_manager.get_hvac_reverse_mapping(
            device_code, device_mode
        )
        if hvac_mode is None:
            if not self.get_device_power(device_code):
                return HVACMode.OFF
            return HVACMode.HEAT

        try:
            result = HVACMode(hvac_mode)
        except (ValueError, TypeError):
            result = HVACMode.HEAT

        return result

    def get_device_fan_mode(self, device_code: str) -> str:
        device_data = self.get_device_data(device_code)
        pc_key = self._config_manager.get_pc_key(device_code, CONFIG_SET_FAN)
        manual_mute = device_data.get(pc_key)

        fan_mode = self._config_manager.get_fan_reverse_mapping(
            device_code, manual_mute
        )

        return fan_mode

    def get_device_power(self, device_code: str) -> bool:
        device_data = self.get_device_data(device_code)
        pc_key = self._config_manager.get_pc_key(device_code, CONFIG_SET_POWER)

        power = device_data.get(pc_key)
        is_on = power == POWER_MODE_ON

        return is_on

    def _get_target_temperature_protocol_code(
        self, device_code: str, hvac_mode: HVACMode
    ):
        target_temperature_pc = self._config_manager.get_hvac_mode_pc_key(
            device_code, hvac_mode, CONFIG_HVAC_TARGET
        )

        _LOGGER.debug(f"Target temp PC {target_temperature_pc}, HA Mode: {hvac_mode}")

        return target_temperature_pc

    def _get_device_product_id(self, device_data: dict):
        param = self._config_manager.get_api_param(APIParam.ProductId)
        product_id = device_data.get(param)

        return product_id

    def _get_device_id(self, device_data: dict):
        param = self._config_manager.get_api_param(APIParam.DeviceCode)
        device_code = device_data.get(param)

        return device_code
