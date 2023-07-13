import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from ..managers.aqua_temp_coordinator import AquaTempCoordinator
from .consts import DOMAIN
from .entity_descriptions import AquaTempEntityDescription

_LOGGER = logging.getLogger(__name__)


def async_setup_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    platform: Platform,
    device_code: str,
    entity_type: type,
    async_add_entities,
):
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        config_manager = coordinator.config_manager

        entities = []

        entity_descriptions = config_manager.get_entity_descriptions(device_code)

        for entity_description in entity_descriptions:
            if entity_description.platform == platform:
                entity = entity_type(entity_description, coordinator, device_code)

                entities.append(entity)

        _LOGGER.debug(f"Setting up {platform} entities: {entities}")

        async_add_entities(entities, True)

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to initialize {platform}, Error: {ex}, Line: {line_number}"
        )


class BaseEntity(CoordinatorEntity):
    _device_id: int
    _entity_description: AquaTempEntityDescription
    _translations: dict

    def __init__(
        self,
        entity_description: AquaTempEntityDescription,
        coordinator: AquaTempCoordinator,
        device_code: str,
    ):
        super().__init__(coordinator)

        self._entity_description = entity_description
        self.entity_description = entity_description

        device_info = coordinator.get_device(device_code)
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        entity_name = coordinator.config_manager.get_entity_name(
            entity_description, device_info
        )

        unique_id = slugify(
            f"{entity_description.platform}_{serial_number}_{entity_description.key}"
        )

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

        self._data = {}
        self._device_code = device_code

    @property
    def device_code(self):
        return self._device_code

    @property
    def local_coordinator(self) -> AquaTempCoordinator:
        return self.coordinator

    @property
    def data(self) -> dict | None:
        return self._data
