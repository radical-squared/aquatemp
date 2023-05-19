"""Platform for climate integration."""
from abc import ABC
import logging
import sys

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TEMPERATURE_UNIT, STATE_ON, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .aqua_temp_coordinator import AquaTempCoordinator
from .consts import (
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
    FAN_MODE_MAPPING,
    HVAC_MODE_MAPPING,
    HVAC_MODE_MAX_TEMP,
    HVAC_MODE_MIN_TEMP,
    HVAC_PC_MAPPING,
    MANUAL_MUTE_MAPPING,
    POWER_MODE_MAPPING,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    climate_entities = [
        AquaTempClimateEntity(device_code, coordinator)
        for device_code in coordinator.api_data
    ]

    async_add_entities(climate_entities)


class AquaTempClimateEntity(CoordinatorEntity, ClimateEntity, ABC):
    """Representation of a climate entity."""

    _name: str | None
    _unique_id: str | None
    _temperature_unit: UnitOfTemperature | None
    _attributes: dict
    _min_temp: float | None
    _max_temp: float | None
    _inlet_temp: float | None
    _outlet_temp: float | None
    _target_temperature: float | None

    def __init__(self, device_code: str, coordinator: AquaTempCoordinator):
        """Initialize the climate entity."""
        super().__init__(coordinator)

        self._device_code = device_code

        self._inlet_temp = None
        self._outlet_temp = None
        self._unique_id = None
        self._min_temp = None
        self._max_temp = None

        self._temperature_unit = None
        self._attribute_map = None
        self._expose_codes = False

        self._target_temperature = None
        self._attributes = {}

        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE
        self._attr_fan_modes = list(FAN_MODE_MAPPING.keys())
        self._attr_hvac_modes = list(HVAC_MODE_MAPPING.keys())

        self._attr_temperature_unit = self._config_data.get(
            CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT
        )
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = FAN_AUTO

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes

    @property
    def inlet_temp(self):
        """Returns the inlet temperature."""
        return self._inlet_temp

    @property
    def outlet_temp(self):
        """Returns the outlet temperature."""
        return self._outlet_temp

    @property
    def name(self):
        """Return the name of the sensor."""
        device_nickname = self._api_data.get("device_nick_name", self._device_code)

        return f"{self.coordinator.name} {device_nickname}"

    def entity_id(self):
        slugify_name = slugify(self.name)
        return f"climate.{slugify_name}"

    @property
    def unique_id(self):
        """Return the device code of the sensor as a unique ID to allow the devices to be edited on the dashboard."""
        device_id = self._api_data.get("device_id")
        slugify_uid = slugify(f"climate_{device_id}")

        return slugify_uid

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    @property
    def _api_data(self):
        return self.coordinator.api_data[self._device_code]

    @property
    def _config_data(self):
        return self.coordinator.config_data

    async def initialize(self):
        try:
            self._name = self.coordinator.name

            self._attr_temperature_unit = self._config_data.get(
                CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(
                f"Failed to initialize session, Error: {ex}, Line: {line_number}"
            )

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")

        try:
            await self.coordinator.set_temperature(self.hvac_mode, temperature)

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        try:
            await self.coordinator.set_hvac_mode(hvac_mode)

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        try:
            await self.coordinator.set_fan_mode(fan_mode)

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    def _handle_coordinator_update(self) -> None:
        """Fetch new state data for the sensor."""
        mode = self._api_data.get("Mode")
        power = self._api_data.get("Power")
        manual_mute = self._api_data.get("Manual-mute")
        current_temperature = self._api_data.get("T02")

        is_power_on = power == STATE_ON

        power_mode = POWER_MODE_MAPPING.get(power)
        hvac_mode = HVAC_PC_MAPPING.get(mode) if is_power_on else HVAC_MODE_OFF

        min_temp_key = HVAC_MODE_MIN_TEMP.get(hvac_mode)
        max_temp_key = HVAC_MODE_MAX_TEMP.get(hvac_mode)

        min_temp = self._api_data.get(min_temp_key, 0)
        max_temp = self._api_data.get(max_temp_key, 0)

        hvac_mode_code = HVAC_MODE_MAPPING.get(hvac_mode)
        hvac_mode_param = f"R0{hvac_mode_code}"
        hvac_mode_temperature_value = self._api_data.get(hvac_mode_param)

        target_temperature = None
        if is_power_on and hvac_mode_temperature_value is not None:
            target_temperature = float(hvac_mode_temperature_value)

        self._attributes["power"] = power_mode

        self._attr_hvac_mode = hvac_mode
        self._attr_target_temperature = target_temperature
        self._attr_fan_mode = MANUAL_MUTE_MAPPING.get(manual_mute)
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp

        if current_temperature is not None:
            self._attr_current_temperature = float(current_temperature)

        self.async_write_ha_state()
