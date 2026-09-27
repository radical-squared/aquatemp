"""Platform for water heater integration."""
from abc import ABC
import logging

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback

from .common.base_entity import BaseEntity, async_setup_base_entry
from .common.consts import (
    CONFIG_SET_MODE,
    CONFIG_SET_POWER,
    CONFIG_SET_TEMPERATURE,
)
from .common.entity_descriptions import AquaTempWaterHeaterEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)

OPERATION_MODE_INTELLIGENT = "Intelligente"
OPERATION_MODE_ECO = "Ecologica"
OPERATION_MODE_HYBRID = "Ibrida"
OPERATION_MODE_FAST = "Riscaldamento rapido"
OPERATION_MODE_OFF = "Off"

OPERATION_LIST = [
    OPERATION_MODE_INTELLIGENT,
    OPERATION_MODE_ECO,
    OPERATION_MODE_HYBRID,
    OPERATION_MODE_FAST,
    OPERATION_MODE_OFF,
]

MODE_TO_OPERATION = {
    "0": OPERATION_MODE_INTELLIGENT,
    "1": OPERATION_MODE_HYBRID,
    "2": OPERATION_MODE_ECO,
    "3": OPERATION_MODE_FAST,
    "4": OPERATION_MODE_FAST,
}

OPERATION_TO_MODE = {
    OPERATION_MODE_INTELLIGENT: "0",
    OPERATION_MODE_HYBRID: "1",
    OPERATION_MODE_ECO: "2",
    OPERATION_MODE_FAST: "3",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.WATER_HEATER,
        AquaTempWaterHeaterEntity,
        async_add_entities,
    )


class AquaTempWaterHeaterEntity(BaseEntity, WaterHeaterEntity, ABC):
    """Representation of a water heater entity."""

    def __init__(
        self,
        entity_description: AquaTempWaterHeaterEntityDescription,
        coordinator: AquaTempCoordinator,
        device_code: str,
    ):
        super().__init__(entity_description, coordinator, device_code)

        self._attr_has_entity_name = True
        self._attr_name = None

        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
            | WaterHeaterEntityFeature.ON_OFF
        )
        self._attr_operation_list = OPERATION_LIST
        self._attr_temperature_unit = (
            coordinator.get_temperature_unit(device_code) or UnitOfTemperature.CELSIUS
        )
        self._attr_min_temp = 30.0
        self._attr_max_temp = 65.0

        # Pre-populate all state attributes immediately from cached coordinator data
        self._update_attributes()

    def _update_attributes(self) -> None:
        """Fetch and update state parameters for the water heater."""
        coordinator = self.local_coordinator
        device_code = self.device_code
        device_data = coordinator.get_device_data(device_code) or {}

        # 1. Power
        is_power_on = coordinator.get_device_power(device_code)

        # 2. Current water temperature (T10 tank temp)
        current_temperature = coordinator.get_device_current_temperature(device_code)
        if current_temperature is None:
            raw_temp = device_data.get("T10") or device_data.get("T02")
            if raw_temp not in (None, ""):
                try:
                    current_temperature = float(str(raw_temp))
                except (ValueError, TypeError):
                    pass
        self._attr_current_temperature = current_temperature

        # 3. Target temperature (R01 setpoint)
        target_temperature = coordinator.get_device_target_temperature(device_code)
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
        self._attr_target_temperature = target_temperature

        # 4. Temperature range
        minimum_temperature = coordinator.get_device_minimum_temperature(device_code)
        maximum_temperature = coordinator.get_device_maximum_temperature(device_code)
        self._attr_min_temp = minimum_temperature if minimum_temperature is not None else 30.0
        self._attr_max_temp = maximum_temperature if maximum_temperature is not None else 65.0

        # 5. Operation Mode
        if not is_power_on:
            self._attr_current_operation = OPERATION_MODE_OFF
        else:
            mode_pc_key = (
                coordinator.config_manager.get_pc_key(device_code, CONFIG_SET_MODE)
                or "Mode"
            )
            raw_mode = str(device_data.get(mode_pc_key, "2")).split(".")[0]
            self._attr_current_operation = MODE_TO_OPERATION.get(raw_mode, OPERATION_MODE_ECO)

        _LOGGER.debug(
            f"WaterHeater update - Device: {device_code}, Power: {is_power_on}, "
            f"Current: {self._attr_current_temperature}, Target: {self._attr_target_temperature}, "
            f"Operation: {self._attr_current_operation}"
        )

    async def async_added_to_hass(self) -> None:
        """Register listeners and write initial state."""
        await super().async_added_to_hass()
        self._update_attributes()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        _LOGGER.debug(f"Water heater set target temperature to: {temperature}")
        if temperature is not None:
            self._attr_target_temperature = float(temperature)
            self.async_write_ha_state()
            await self.local_coordinator.set_temperature(self.device_code, float(temperature))

    async def async_set_operation_mode(self, operation_mode: str):
        """Set new operation mode."""
        _LOGGER.debug(f"Water heater set operation mode to: {operation_mode}")
        if operation_mode == OPERATION_MODE_OFF:
            self._attr_current_operation = OPERATION_MODE_OFF
            self.async_write_ha_state()
            await self.local_coordinator.set_power(self.device_code, False)
        else:
            mode_value = OPERATION_TO_MODE.get(operation_mode, "2")
            self._attr_current_operation = operation_mode
            self.async_write_ha_state()
            await self.local_coordinator.set_operation_mode(self.device_code, mode_value)

    async def async_turn_on(self, **kwargs):
        """Turn the water heater on."""
        _LOGGER.debug("Water heater turn on")
        await self.local_coordinator.set_power(self.device_code, True)

    async def async_turn_off(self, **kwargs):
        """Turn the water heater off."""
        _LOGGER.debug("Water heater turn off")
        await self.local_coordinator.set_power(self.device_code, False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        self._update_attributes()
        self.async_write_ha_state()
