import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import DEVICE_PRODUCT_ID, DOMAIN, SIGNAL_AQUA_TEMP_DEVICE_NEW
from .common.entity_descriptions import AquaTempSensorEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    def _create(
        device_code: str, entity_description_key: str, coordinator: AquaTempCoordinator
    ) -> AquaTempSensorEntity:
        product_configuration_manager = coordinator.product_configuration_manager

        device_data = coordinator.get_device_data(device_code)
        product_id = device_data.get(DEVICE_PRODUCT_ID)

        entity_description = product_configuration_manager.find_entity_description(
            product_id, entity_description_key, Platform.SENSOR
        )

        entity = AquaTempSensorEntity(device_code, entity_description, coordinator)

        return entity

    @callback
    def _async_device_new(device_code):
        coordinator = hass.data[DOMAIN][entry.entry_id]
        product_configuration_manager = coordinator.product_configuration_manager

        product_configuration_manager.async_handle_discovered_device(
            device_code,
            coordinator,
            Platform.SENSOR,
            _create,
            async_add_entities,
        )

    """Set up the binary sensor platform."""
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_AQUA_TEMP_DEVICE_NEW, _async_device_new)
    )


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

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")
        device_data = coordinator.get_device_data(self._device_code)

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        device_id = device_data.get("device_id")
        unique_id = slugify(f"{entity_description.platform}_{slugify_name}_{device_id}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        self._attr_device_class = entity_description.device_class
        self._attr_native_unit_of_measurement = (
            entity_description.native_unit_of_measurement
        )

        if entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            self._attr_native_unit_of_measurement = (
                self._local_coordinator.get_temperature_unit(device_code)
            )

    @property
    def _local_coordinator(self) -> AquaTempCoordinator:
        return self.coordinator

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        device_data = self._local_coordinator.get_device_data(self._device_code)

        state = device_data.get(self.entity_description.key)

        if isinstance(state, str):
            state = float(state)

        self._attr_native_value = state

        self.async_write_ha_state()
