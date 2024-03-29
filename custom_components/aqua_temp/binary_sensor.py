import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .common.base_entity import BaseEntity, async_setup_base_entry
from .common.consts import API_STATUS
from .common.entity_descriptions import AquaTempBinarySensorEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.BINARY_SENSOR,
        AquaTempBinarySensorEntity,
        async_add_entities,
    )


class AquaTempBinarySensorEntity(BaseEntity, BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: AquaTempBinarySensorEntityDescription,
        coordinator: AquaTempCoordinator,
        device_code: str,
    ):
        super().__init__(entity_description, coordinator, device_code)

        self._attr_device_class = entity_description.device_class
        self._entity_attributes = entity_description.attributes
        self._entity_on_value = entity_description.on_value

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        device_data = self.local_coordinator.get_device_data(self.device_code)

        if self.entity_description.key == API_STATUS:
            state = self.local_coordinator.api_status

        else:
            state = device_data.get(self.entity_description.key)

        is_on = str(state).lower() == str(self._entity_on_value).lower()

        attributes = {}
        if self._entity_attributes is not None:
            for attribute_key in self._entity_attributes:
                value = device_data.get(attribute_key)

                attributes[attribute_key] = value

        self._attr_is_on = is_on
        self._attr_extra_state_attributes = attributes

        self.async_write_ha_state()
