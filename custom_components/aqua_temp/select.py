from abc import ABC
import logging

from homeassistant.components.select import (
    DOMAIN as SELECT_DOMAIN,
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import DOMAIN
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device_code in coordinator.api_data:
        entity = AquaTempSelectEntity(device_code, coordinator)

        entities.append(entity)

    _LOGGER.debug(f"Setting up sensor entities: {entities}")

    async_add_entities(entities, True)


class AquaTempSelectEntity(CoordinatorEntity, SelectEntity, ABC):
    """Representation of a sensor."""

    def __init__(self, device_code: str, coordinator: AquaTempCoordinator):
        super().__init__(coordinator)

        self._device_code = device_code
        self._api_data = self.coordinator.api_data[self._device_code]
        self._config_data = self.coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")

        entity_name = f"{device_name} Temperature Unit"

        device_id = self._api_data.get("device_id")
        slugify_uid = slugify(f"{SELECT_DOMAIN}_temp_unit_{device_id}")

        entity_description = SelectEntityDescription(slugify_uid)
        entity_description.name = entity_name
        entity_description.entity_category = EntityCategory.CONFIG
        entity_description.options = [
            UnitOfTemperature.CELSIUS,
            UnitOfTemperature.FAHRENHEIT,
        ]

        self.entity_description = entity_description
        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = slugify_uid

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        temperature_unit = self.coordinator.get_temperature_unit(self._device_code)

        return temperature_unit

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.set_temperature_unit(self._device_code, option)

        await self.coordinator.async_request_refresh()
