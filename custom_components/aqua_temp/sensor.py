import logging
import sys

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import ALL_ENTITIES, DOMAIN
from .common.entity_descriptions import AquaTempSensorEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platform."""
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        entities = []
        entity_descriptions = []

        for entity_description in ALL_ENTITIES:
            if entity_description.platform == Platform.SENSOR:
                entity_descriptions.append(entity_description)

        for device_code in coordinator.api_data:
            for entity_description in entity_descriptions:
                entity = AquaTempSensorEntity(
                    device_code, entity_description, coordinator
                )

                entities.append(entity)

        _LOGGER.debug(f"Setting up sensor entities: {entities}")

        async_add_entities(entities, True)
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to initialize sensor, Error: {ex}, Line: {line_number}")


class AquaTempSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        device_code: str,
        entity_description: AquaTempSensorEntityDescription,
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

        self.entity_description: AquaTempSensorEntityDescription = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        self._attr_device_class = entity_description.device_class
        self._attr_native_unit_of_measurement = entity_description.native_unit_of_measurement

        if entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            self._attr_native_unit_of_measurement = (
                self.coordinator.get_temperature_unit(device_code)
            )

    def _handle_coordinator_update(self) -> None:
        """Fetch new state data for the sensor."""
        state: float | int | str | None = self._api_data.get(
            self.entity_description.key
        )

        if isinstance(state, str):
            state = float(state)

        self._attr_native_value = state

        self.async_write_ha_state()
