import logging

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import DOMAIN
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device_code in coordinator.api_data:
        status_entity = AquaTempStatusEntity(device_code, coordinator)
        fault_entity = AquaTempFaultEntity(device_code, coordinator)

        entities.extend([status_entity, fault_entity])

    _LOGGER.debug(f"Setting up binary sensor entities: {entities}")

    async_add_entities(entities, True)


class AquaTempStatusEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self, device_code: str, coordinator: AquaTempCoordinator):
        super().__init__(coordinator)

        self._key = "device_status"
        self._device_code = device_code
        self._api_data = self.coordinator.api_data[self._device_code]
        self._config_data = self.coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")

        entity_name = f"{self.coordinator.name} {device_name} Status"

        slugify_name = slugify(entity_name)

        device_id = self._api_data.get("device_id")
        slugify_uid = slugify(f"{BINARY_SENSOR_DOMAIN}_{slugify_name}_{device_id}")

        entity_description = BinarySensorEntityDescription(slugify_uid)
        entity_description.name = entity_name
        entity_description.device_class = BinarySensorDeviceClass.CONNECTIVITY

        self.entity_description = entity_description
        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = slugify_uid

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        status = self._api_data.get(self._key)
        is_on = status == "ONLINE"

        return is_on


class AquaTempFaultEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self, device_code: str, coordinator: AquaTempCoordinator):
        super().__init__(coordinator)

        self._key = "is_fault"
        self._device_code = device_code
        self._api_data = self.coordinator.api_data[self._device_code]
        self._config_data = self.coordinator.config_data

        device_nickname = self._api_data.get("device_nick_name", device_code)
        entity_name = f"{self.coordinator.name} {device_nickname} Fault"

        slugify_name = slugify(entity_name)

        device_id = self._api_data.get("device_id")
        slugify_uid = slugify(f"{BINARY_SENSOR_DOMAIN}_{slugify_name}_{device_id}")

        entity_description = BinarySensorEntityDescription(slugify_uid)
        entity_description.name = entity_name
        entity_description.device_class = BinarySensorDeviceClass.CONNECTIVITY

        self.entity_description = entity_description

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        is_on = self._api_data.get(self._key, False)

        return is_on
