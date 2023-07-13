import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import BaseEntity, async_setup_entities
from .common.consts import SIGNAL_AQUA_TEMP_DEVICE_NEW
from .common.entity_descriptions import AquaTempBinarySensorEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    @callback
    def _async_device_new(entry_id: str, device_code: str):
        if entry.entry_id != entry_id:
            return

        async_setup_entities(
            hass,
            entry,
            Platform.BINARY_SENSOR,
            device_code,
            AquaTempBinarySensorEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_AQUA_TEMP_DEVICE_NEW, _async_device_new)
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
        status = device_data.get(self.entity_description.key)

        attributes = {}
        if self._entity_attributes is not None:
            for attribute_key in self._entity_attributes:
                value = device_data.get(attribute_key)

                attributes[attribute_key] = value

        self._attr_is_on = status == self._entity_on_value
        self._attr_extra_state_attributes = attributes

        self.async_write_ha_state()
