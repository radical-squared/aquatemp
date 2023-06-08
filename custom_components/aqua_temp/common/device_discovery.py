import logging
import sys
from typing import Callable

from homeassistant.const import Platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..managers.aqua_temp_coordinator import AquaTempCoordinator
from .entity_descriptions import ALL_ENTITIES

_LOGGER = logging.getLogger(__name__)


def async_handle_discovered_device(
    device_code: str,
    coordinator: AquaTempCoordinator,
    platform: Platform,
    entity_initializer: Callable[
        [str, str, AquaTempCoordinator],
        Entity,
    ],
    async_add_entities: AddEntitiesCallback,
):
    try:
        entities = []
        entity_descriptions = []

        for entity_description in ALL_ENTITIES:
            if entity_description.platform == platform:
                entity_descriptions.append(entity_description)

        for entity_description in entity_descriptions:
            entity = entity_initializer(
                device_code, entity_description.key, coordinator
            )

            entities.append(entity)

        _LOGGER.debug(f"Setting up {platform} entities: {entities}")

        async_add_entities(entities, True)

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to initialize {platform}, Error: {ex}, Line: {line_number}"
        )


def find_entity_description(key: str, platform: Platform):
    entity_descriptions = [
        entity_description
        for entity_description in ALL_ENTITIES
        if entity_description.platform == platform and entity_description.key == key
    ]

    result = None if len(entity_descriptions) == 0 else entity_descriptions[0]

    return result
