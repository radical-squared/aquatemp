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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import (
    ALL_ENTITIES,
    DOMAIN,
    HVAC_MODE_MAPPING,
    HVAC_PC_MAPPING,
    MANUAL_MUTE_MAPPING,
    POWER_MODE_ON,
)
from .common.entity_descriptions import AquaTempClimateEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    entity_descriptions = []

    for entity_description in ALL_ENTITIES:
        if entity_description.platform == Platform.CLIMATE:
            entity_descriptions.append(entity_description)

    for device_code in coordinator.api_data:
        for entity_description in entity_descriptions:
            entity = AquaTempClimateEntity(device_code, entity_description, coordinator)

            entities.append(entity)

    _LOGGER.debug(f"Setting up climate entities: {entities}")

    async_add_entities(entities, True)


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

        self._api_data = coordinator.api_data[device_code]
        self._config_data = coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        device_id = self._api_data.get("device_id")
        unique_id = slugify(f"{entity_description.platform}_{slugify_name}_{device_id}")

        self.entity_description: AquaTempClimateEntityDescription = entity_description

        self._device_code = device_code

        self._attr_device_info = device_info
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE
        self._attr_fan_modes = entity_description.fan_modes
        self._attr_hvac_modes = entity_description.hvac_modes

        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = FAN_AUTO

        self._attr_temperature_unit = self.coordinator.get_temperature_unit(device_code)
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")

        try:
            await self.coordinator.set_temperature(
                self._device_code, self.hvac_mode, temperature
            )

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        try:
            await self.coordinator.set_hvac_mode(self._device_code, hvac_mode)

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        try:
            await self.coordinator.set_fan_mode(self._device_code, fan_mode)

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    def _handle_coordinator_update(self) -> None:
        """Fetch new state data for the sensor."""
        entity_description = self.entity_description

        mode = self._api_data.get(entity_description.key)
        power = self._api_data.get(entity_description.power_key)
        manual_mute = self._api_data.get(entity_description.fan_mode_key)
        current_temperature = self._api_data.get(
            entity_description.current_temperature_key
        )

        is_power_on = power == POWER_MODE_ON

        hvac_mode = HVAC_PC_MAPPING.get(mode) if is_power_on else HVACMode.OFF

        if entity_description.minimum_temperature_keys is not None:
            min_temp_key = entity_description.minimum_temperature_keys.get(hvac_mode)
            min_temp = self._api_data.get(min_temp_key, 0)

            self._attr_min_temp = float(str(min_temp))

        if entity_description.maximum_temperature_keys is not None:
            max_temp_key = entity_description.maximum_temperature_keys.get(hvac_mode)
            max_temp = self._api_data.get(max_temp_key, 0)

            self._attr_max_temp = float(str(max_temp))

        hvac_mode_code = HVAC_MODE_MAPPING.get(hvac_mode)
        hvac_mode_param = f"R0{hvac_mode_code}"
        hvac_mode_temperature_value = self._api_data.get(hvac_mode_param)

        target_temperature = None
        if is_power_on and hvac_mode_temperature_value is not None:
            target_temperature = float(hvac_mode_temperature_value)

        self._attr_hvac_mode = hvac_mode
        self._attr_fan_mode = MANUAL_MUTE_MAPPING.get(manual_mute)
        self._attr_target_temperature = float(str(target_temperature))

        if current_temperature is not None:
            self._attr_current_temperature = float(str(current_temperature))

        _LOGGER.debug(f"{entity_description.key}: {mode}")
        _LOGGER.debug(f"{entity_description.power_key}: {power}")
        _LOGGER.debug(f"{entity_description.fan_mode_key}: {manual_mute}")
        _LOGGER.debug(
            f"{entity_description.current_temperature_key}: {current_temperature}"
        )
        _LOGGER.debug(f"is_power_on: {is_power_on}")

        _LOGGER.debug(f"_attr_hvac_mode: {self._attr_hvac_mode}")
        _LOGGER.debug(f"_attr_target_temperature: {self._attr_target_temperature}")
        _LOGGER.debug(f"_attr_fan_mode: {self._attr_fan_mode}")
        _LOGGER.debug(f"_attr_min_temp: {self._attr_min_temp}")
        _LOGGER.debug(f"_attr_max_temp: {self._attr_max_temp}")

        self.async_write_ha_state()
