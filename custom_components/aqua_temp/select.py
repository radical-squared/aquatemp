from abc import ABC
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import BaseEntity, async_setup_entities
from .common.consts import SIGNAL_AQUA_TEMP_DEVICE_NEW
from .common.entity_descriptions import AquaTempSelectEntityDescription
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
            Platform.SELECT,
            device_code,
            AquaTempSelectEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_AQUA_TEMP_DEVICE_NEW, _async_device_new)
    )


class AquaTempSelectEntity(BaseEntity, SelectEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: AquaTempSelectEntityDescription,
        coordinator: AquaTempCoordinator,
        device_code: str,
    ):
        super().__init__(entity_description, coordinator, device_code)

        self._attr_current_option = self._get_temperature_unit()

    def _get_temperature_unit(self):
        coordinator = self.local_coordinator
        temperature_unit = coordinator.get_temperature_unit(self._device_code)

        return temperature_unit

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.local_coordinator.set_temperature_unit(self._device_code, option)

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        self._attr_current_option = self._get_temperature_unit()

        self.async_write_ha_state()
