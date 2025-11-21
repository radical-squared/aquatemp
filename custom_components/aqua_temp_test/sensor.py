import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .common.base_entity import BaseEntity, async_setup_base_entry
from .common.entity_descriptions import AquaTempSensorEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.SENSOR,
        AquaTempSensorEntity,
        async_add_entities,
    )


class AquaTempSensorEntity(BaseEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: AquaTempSensorEntityDescription,
        coordinator: AquaTempCoordinator,
        device_code: str,
    ):
        super().__init__(entity_description, coordinator, device_code)

        self._attr_device_class = entity_description.device_class
        self._attr_native_unit_of_measurement = (
            entity_description.native_unit_of_measurement
        )

        if entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            self._attr_native_unit_of_measurement = coordinator.get_temperature_unit(
                device_code
            )

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        device_data = self.local_coordinator.get_device_data(self.device_code)

        state = device_data.get(self.entity_description.key)

        if isinstance(state, str):
            state = float(state)

        self._attr_native_value = state

        self.async_write_ha_state()
