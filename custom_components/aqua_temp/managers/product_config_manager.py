from copy import copy
import json
import logging
import os
import sys
from typing import Callable

from homeassistant.const import EntityCategory, Platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .. import AquaTempCoordinator
from ..common.consts import DEVICE_PRODUCT_ID, PRODUCT_IDS
from ..common.entity_descriptions import (
    DEFAULT_ENTITY_DESCRIPTIONS,
    AquaTempBinarySensorEntityDescription,
    AquaTempSensorEntityDescription,
)

_LOGGER = logging.getLogger(__name__)


class ProductConfigurationManager:
    _entity_descriptions: dict
    platforms: list[str]

    def __init__(self):
        self._entity_descriptions = {}
        self.platforms = []

    def initialize(self):
        self._load_product_configuration("default")

        for product_id in PRODUCT_IDS:
            has_dedicated_config = PRODUCT_IDS.get()

            if has_dedicated_config:
                self._load_product_configuration(product_id)

    def get_entity_descriptions(self, product_id):
        result = self._entity_descriptions.get(product_id)

        return result

    def async_handle_discovered_device(
        self,
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

            device_data = coordinator.get_device_data(device_code)
            product_id = device_data.get(DEVICE_PRODUCT_ID)
            entity_descriptions = self.get_entity_descriptions(product_id)

            for entity_description in entity_descriptions:
                if entity_description.platform == platform:
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

    def find_entity_description(self, product_id: str, key: str, platform: Platform):
        entity_descriptions = self.get_entity_descriptions(product_id)

        entity_descriptions = [
            entity_description
            for entity_description in entity_descriptions
            if entity_description.platform == platform and entity_description.key == key
        ]

        result = None if len(entity_descriptions) == 0 else entity_descriptions[0]

        return result

    def _load_product_configuration(self, product_id: str = "default"):
        entities = copy(DEFAULT_ENTITY_DESCRIPTIONS)
        file_path = os.path.join(
            os.path.dirname(__file__), f"../parameters/{product_id}.json"
        )

        with open(file_path) as file:
            json_str = file.read()

            json_data = json.loads(json_str)

            for data_item in json_data:
                platform = data_item.get("platform")

                if platform == Platform.SENSOR:
                    sensor_entity = AquaTempSensorEntityDescription(
                        key=data_item.get("key"),
                        name=data_item.get("name"),
                        device_class=data_item.get("device_class"),
                        native_unit_of_measurement=data_item.get("unit_of_measurement"),
                        entity_category=EntityCategory.DIAGNOSTIC,
                    )

                    entities.append(sensor_entity)

                elif platform == Platform.BINARY_SENSOR:
                    binary_sensor_entity = AquaTempBinarySensorEntityDescription(
                        key=data_item.get("key"),
                        name=data_item.get("name"),
                        device_class=data_item.get("device_class"),
                        on_value=data_item.get("on_value"),
                        entity_category=EntityCategory.DIAGNOSTIC,
                    )

                    entities.append(binary_sensor_entity)

        self._update_platforms(entities)

        self._entity_descriptions[product_id] = entities

    def _update_platforms(self, entity_descriptions):
        for entity_description in entity_descriptions:
            if (
                entity_description.platform not in self.platforms
                and entity_description.platform is not None
            ):
                self.platforms.append(entity_description.platform)
