from abc import ABC
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant

from .common.base_entity import BaseEntity, async_setup_base_entry
from .common.entity_descriptions import AquaTempSelectEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.SELECT,
        AquaTempSelectEntity,
        async_add_entities,
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

        self._attr_options = self._get_options()
        self._attr_current_option = self._get_current_option()

    def _get_options(self):
        if self._entity_description.key == "controller_mode":
            return list(
                self.local_coordinator.config_manager.get_mode_profiles(
                    self._device_code
                )
            )
        return [UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT]

    def _get_current_option(self):
        if self._entity_description.key == "controller_mode":
            return self.local_coordinator.get_mode_profile(self._device_code)
        return self._get_temperature_unit()

    def _get_temperature_unit(self):
        coordinator = self.local_coordinator
        temperature_unit = coordinator.get_temperature_unit(self._device_code)

        return temperature_unit

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self._entity_description.key == "controller_mode":
            await self.local_coordinator.set_mode_profile(self._device_code, option)
        else:
            await self.local_coordinator.set_temperature_unit(self._device_code, option)

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        self._attr_current_option = self._get_current_option()

        self.async_write_ha_state()
