"""Platform for climate integration."""
from abc import ABC
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback

from .common.base_entity import BaseEntity, async_setup_base_entry
from .common.consts import CONFIG_SET_TEMPERATURE
from .common.entity_descriptions import AquaTempClimateEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.CLIMATE,
        AquaTempClimateEntity,
        async_add_entities,
    )


class AquaTempClimateEntity(BaseEntity, ClimateEntity, ABC):
    """Representation of a climate entity."""

    _attributes: dict

    def __init__(
        self,
        entity_description: AquaTempClimateEntityDescription,
        coordinator: AquaTempCoordinator,
        device_code: str,
    ):
        """Initialize the climate entity."""
        super().__init__(entity_description, coordinator, device_code)

        self._enable_turn_on_off_backwards_compatibility = False

        self._attr_supported_features = (
            ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
        )
        self._attr_fan_modes = list(coordinator.get_fan_modes(device_code))
        self._attr_hvac_modes = list(coordinator.get_hvac_modes(device_code))

        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = FAN_AUTO

        self._attr_temperature_unit = (
            coordinator.get_temperature_unit(device_code) or UnitOfTemperature.CELSIUS
        )
        self._attr_min_temp = 30.0
        self._attr_max_temp = 65.0

        # Pre-populate state attributes immediately
        self._update_attributes()

    def _update_attributes(self) -> None:
        """Fetch new state parameters for the climate entity."""
        coordinator = self.local_coordinator
        device_code = self.device_code
        device_data = coordinator.get_device_data(device_code) or {}

        hvac_mode = coordinator.get_device_hvac_mode(device_code)
        is_power_on = coordinator.get_device_power(device_code)
        fan_mode = coordinator.get_device_fan_mode(device_code)
        current_temperature = coordinator.get_device_current_temperature(device_code)
        target_temperature = coordinator.get_device_target_temperature(device_code)
        minimum_temperature = coordinator.get_device_minimum_temperature(device_code)
        maximum_temperature = coordinator.get_device_maximum_temperature(device_code)

        if not is_power_on:
            hvac_mode = HVACMode.OFF

        if minimum_temperature is None:
            minimum_temperature = 30.0
        if maximum_temperature is None:
            maximum_temperature = 65.0

        if target_temperature is None:
            temp_pc_key = coordinator.config_manager.get_pc_key(
                device_code, CONFIG_SET_TEMPERATURE
            )
            raw_target = (
                device_data.get(temp_pc_key)
                if temp_pc_key
                else None
            ) or device_data.get("R01") or device_data.get("Set_Temp")
            if raw_target not in (None, ""):
                try:
                    target_temperature = float(str(raw_target))
                except (ValueError, TypeError):
                    pass

        if current_temperature is None:
            raw_curr = device_data.get("T10") or device_data.get("T02")
            if raw_curr not in (None, ""):
                try:
                    current_temperature = float(str(raw_curr))
                except (ValueError, TypeError):
                    pass

        self._attr_min_temp = minimum_temperature
        self._attr_max_temp = maximum_temperature
        self._attr_hvac_mode = hvac_mode
        self._attr_fan_mode = fan_mode
        self._attr_target_temperature = target_temperature
        self._attr_current_temperature = current_temperature

        _LOGGER.debug(
            f"Climate update - Device: {device_code}, Mode: {self._attr_hvac_mode}, "
            f"Current: {self._attr_current_temperature}, Target: {self._attr_target_temperature}"
        )

    async def async_added_to_hass(self) -> None:
        """Register listeners and write initial state."""
        await super().async_added_to_hass()
        self._update_attributes()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        _LOGGER.debug(f"Set target temperature to: {temperature}")

        await self.local_coordinator.set_temperature(self.device_code, temperature)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug(f"Set HVAC Mode to: {hvac_mode}")

        await self.local_coordinator.set_hvac_mode(self.device_code, hvac_mode)

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        _LOGGER.debug(f"Set Fan Mode to: {fan_mode}")

        await self.local_coordinator.set_fan_mode(self.device_code, fan_mode)

    async def async_turn_on(self):
        """Turn the entity on."""
        modes = [m for m in self._attr_hvac_modes if m != HVACMode.OFF]
        mode_to_set = modes[0] if modes else HVACMode.HEAT
        await self.async_set_hvac_mode(mode_to_set)

    async def async_turn_off(self):
        """Turn the entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        self._update_attributes()
        self.async_write_ha_state()
