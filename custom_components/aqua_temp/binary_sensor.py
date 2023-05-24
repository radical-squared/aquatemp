import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import ALL_ENTITIES, DOMAIN
from .common.entity_descriptions import AquaTempBinarySensorEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    entity_descriptions = []

    for entity_description in ALL_ENTITIES:
        if entity_description.platform == Platform.BINARY_SENSOR:
            entity_descriptions.append(entity_description)

    for device_code in coordinator.api_data:
        for entity_description in entity_descriptions:
            entity = AquaTempBinarySensorEntity(
                device_code, entity_description, coordinator
            )

            entities.append(entity)

    _LOGGER.debug(f"Setting up binary sensor entities: {entities}")

    async_add_entities(entities, True)


class AquaTempBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        device_code: str,
        entity_description: AquaTempBinarySensorEntityDescription,
        coordinator: AquaTempCoordinator,
    ):
        super().__init__(coordinator)

        self._device_code = device_code
        self._api_data = self.coordinator.api_data[self._device_code]
        self._config_data = self.coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        device_id = self._api_data.get("device_id")
        unique_id = slugify(f"{entity_description.platform}_{slugify_name}_{device_id}")

        self.entity_description: AquaTempBinarySensorEntityDescription = (
            entity_description
        )

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        self._attr_device_class = entity_description.device_class

    @property
    def state_attributes(self) -> dict[str, Any] | None:
        attributes = {}
        if self.entity_description.attributes is not None:
            for attribute_key in self.entity_description.attributes:
                value = self._api_data.get(attribute_key)

                attributes[attribute_key] = value

        return attributes

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        status = self._api_data.get(self.entity_description.key)

        is_on = status == self.entity_description.on_value

        return is_on
