import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from ..managers.aqua_temp_coordinator import AquaTempCoordinator
from .consts import ADD_COMPONENT_SIGNALS, DOMAIN
from .entity_descriptions import AquaTempEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_base_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    platform: Platform,
    entity_type: type,
    async_add_entities,
):
    @callback
    def _async_handle_device(entry_id: str, device_code: str):
        if entry.entry_id != entry_id:
            return

        try:
            coordinator = hass.data[DOMAIN][entry.entry_id]

            config_manager = coordinator.config_manager

            entity_descriptions = config_manager.get_entity_descriptions(device_code)

            entities = [
                entity_type(entity_description, coordinator, device_code)
                for entity_description in entity_descriptions
                if entity_description.platform == platform
            ]

            _LOGGER.debug(f"Setting up {platform} entities: {entities}")

            async_add_entities(entities, True)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize {platform}, Error: {ex}, Line: {line_number}"
            )

    for add_component_signal in ADD_COMPONENT_SIGNALS:
        entry.async_on_unload(
            async_dispatcher_connect(hass, add_component_signal, _async_handle_device)
        )


class BaseEntity(CoordinatorEntity):
    _device_code: str
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

        entity_name = coordinator.config_manager.get_entity_name(
            entity_description, device_info
        )

        unique_id_parts = [
            DOMAIN,
            entity_description.platform,
            entity_description.key,
            device_code,
        ]

        unique_id = slugify("_".join(unique_id_parts))

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
