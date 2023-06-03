"""Platform for climate integration."""
from abc import ABC
import logging
import sys

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import DOMAIN, SIGNAL_AQUA_TEMP_DEVICE_NEW
from .common.device_discovery import (
    async_handle_discovered_device,
    find_entity_description,
)
from .common.entity_descriptions import AquaTempClimateEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    def _create(
        device_code: str, entity_description_key: str, coordinator: AquaTempCoordinator
    ) -> AquaTempClimateEntity:
        entity_description = find_entity_description(
            entity_description_key, Platform.CLIMATE
        )

        entity = AquaTempClimateEntity(device_code, entity_description, coordinator)

        return entity

    @callback
    def _async_device_new(device_code):
        coordinator = hass.data[DOMAIN][entry.entry_id]

        async_handle_discovered_device(
            device_code,
            coordinator,
            Platform.CLIMATE,
            _create,
            async_add_entities,
        )

    """Set up the binary sensor platform."""
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_AQUA_TEMP_DEVICE_NEW, _async_device_new)
    )


class AquaTempClimateEntity(CoordinatorEntity, ClimateEntity, ABC):
    """Representation of a climate entity."""

    _attributes: dict

    def __init__(
        self,
        device_code: str,
        entity_description: AquaTempClimateEntityDescription,
        coordinator: AquaTempCoordinator,
    ):
        """Initialize the climate entity."""
        super().__init__(coordinator)

        self._api = coordinator.api_data
        self._config_data = coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")
        device_data = coordinator.get_device_data(device_code)

        entity_name = f"{device_name}"

        slugify_name = slugify(entity_name)

        device_id = device_data.get("device_id")
        unique_id = slugify(f"{entity_description.platform}_{slugify_name}_{device_id}")

        self.entity_description = entity_description

        self._device_code = device_code

        self._attr_device_info = device_info
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE
        self._attr_fan_modes = entity_description.fan_modes
        self._attr_hvac_modes = entity_description.hvac_modes

        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = FAN_AUTO

        self._attr_temperature_unit = coordinator.get_temperature_unit(device_code)
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

        self._minimum_temperature_keys = entity_description.minimum_temperature_keys
        self._maximum_temperature_keys = entity_description.maximum_temperature_keys

    @property
    def _local_coordinator(self) -> AquaTempCoordinator:
        return self.coordinator

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")

        try:
            await self._local_coordinator.set_temperature(
                self._device_code, temperature
            )

            await self._local_coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        try:
            _LOGGER.debug(f"Set HVAC Mode to: {hvac_mode}")

            await self._local_coordinator.set_hvac_mode(self._device_code, hvac_mode)

            await self._local_coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        try:
            _LOGGER.debug(f"Set Fan Mode to: {fan_mode}")

            await self._local_coordinator.set_fan_mode(self._device_code, fan_mode)

            await self._local_coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    def _handle_coordinator_update(self) -> None:
        """Fetch new state data for the sensor."""
        coordinator = self._local_coordinator
        device_code = self._device_code
        device_data = coordinator.get_device_data(device_code)

        hvac_mode = coordinator.get_device_hvac_mode(device_code)
        is_power_on = coordinator.get_device_power(device_code)
        fan_mode = coordinator.get_device_fan_mode(device_code)
        current_temperature = coordinator.get_device_current_temperature(device_code)
        target_temperature = coordinator.get_device_target_temperature(device_code)

        if not is_power_on:
            hvac_mode = HVACMode.OFF
            target_temperature = None

        if self._minimum_temperature_keys is not None:
            min_temp_key = self._minimum_temperature_keys.get(hvac_mode)
            min_temp = device_data.get(min_temp_key, 0)

            self._attr_min_temp = float(str(min_temp))

        if self._maximum_temperature_keys is not None:
            max_temp_key = self._maximum_temperature_keys.get(hvac_mode)
            max_temp = device_data.get(max_temp_key, 0)

            self._attr_max_temp = float(str(max_temp))

        self._attr_hvac_mode = hvac_mode
        self._attr_fan_mode = fan_mode

        if target_temperature is not None:
            self._attr_target_temperature = float(str(target_temperature))

        if current_temperature is not None:
            self._attr_current_temperature = float(str(current_temperature))

        _LOGGER.debug(f"_attr_hvac_mode: {self._attr_hvac_mode}")
        _LOGGER.debug(f"_attr_target_temperature: {self._attr_target_temperature}")
        _LOGGER.debug(f"_attr_fan_mode: {self._attr_fan_mode}")
        _LOGGER.debug(f"_attr_min_temp: {self._attr_min_temp}")
        _LOGGER.debug(f"_attr_max_temp: {self._attr_max_temp}")

        self.async_write_ha_state()
