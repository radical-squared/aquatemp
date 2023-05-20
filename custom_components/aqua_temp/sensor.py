import logging

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import DOMAIN, PROTOCOL_CODES
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Setup the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device_code in coordinator.api_data:
        temperature_entities = [
            AquaTempTemperatureEntity(device_code, key, coordinator)
            for key in PROTOCOL_CODES
            if key.startswith("T") and PROTOCOL_CODES.get(key) is not None
        ]

        entities.extend(temperature_entities)

    _LOGGER.debug(f"Setting up sensor entities: {entities}")

    async_add_entities(entities, True)


class AquaTempTemperatureEntity(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(self, device_code: str, key: str, coordinator: AquaTempCoordinator):
        super().__init__(coordinator)

        self._key = key
        self._device_code = device_code
        self._api_data = self.coordinator.api_data[self._device_code]
        self._config_data = self.coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")

        entity_name = f"{device_name} {PROTOCOL_CODES.get(key)}"

        device_id = self._api_data.get("device_id")
        slugify_uid = slugify(f"{SENSOR_DOMAIN}_{key}_{device_id}")

        native_unit = self.coordinator.get_temperature_unit(device_code)

        entity_description = SensorEntityDescription(slugify_uid)
        entity_description.name = entity_name
        entity_description.device_class = SensorDeviceClass.TEMPERATURE
        entity_description.native_unit_of_measurement = native_unit

        self.entity_description = entity_description
        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = slugify_uid

    @property
    def native_value(self) -> float | int | str | None:
        """Return current state."""
        state: float | int | str | None = self._api_data.get(self._key)

        if isinstance(state, str):
            state = float(state)

        return state
