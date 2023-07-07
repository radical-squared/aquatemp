from abc import ABC
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import DOMAIN, SIGNAL_AQUA_TEMP_DEVICE_NEW
from .common.entity_descriptions import AquaTempSelectEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    def _create(
        device_code: str, entity_description_key: str, coordinator: AquaTempCoordinator
    ) -> AquaTempSelectEntity:
        config_manager = coordinator.config_manager

        entity_description = config_manager.find_entity_description(
            device_code, entity_description_key, Platform.SELECT
        )

        entity = AquaTempSelectEntity(device_code, entity_description, coordinator)

        return entity

    @callback
    def _async_device_new(device_code):
        coordinator = hass.data[DOMAIN][entry.entry_id]
        product_configuration_manager = coordinator.product_configuration_manager

        product_configuration_manager.async_handle_discovered_device(
            device_code,
            coordinator,
            Platform.SELECT,
            _create,
            async_add_entities,
        )

    """Set up the binary sensor platform."""
    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_AQUA_TEMP_DEVICE_NEW, _async_device_new)
    )


class AquaTempSelectEntity(CoordinatorEntity, SelectEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        device_code: str,
        entity_description: AquaTempSelectEntityDescription,
        coordinator: AquaTempCoordinator,
    ):
        super().__init__(coordinator)

        self._device_code = device_code

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")
        device_data = coordinator.get_device_data(device_code)

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        device_id = device_data.get("device_id")
        unique_id = slugify(f"{entity_description.platform}_{slugify_name}_{device_id}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        self._attr_current_option = self._get_temperature_unit()

    @property
    def _local_coordinator(self) -> AquaTempCoordinator:
        return self.coordinator

    def _get_temperature_unit(self):
        coordinator = self._local_coordinator
        temperature_unit = coordinator.get_temperature_unit(self._device_code)

        return temperature_unit

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._local_coordinator.set_temperature_unit(self._device_code, option)

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        self._attr_current_option = self._get_temperature_unit()

        self.async_write_ha_state()
