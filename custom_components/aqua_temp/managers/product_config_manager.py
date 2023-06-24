from copy import copy
import json
import logging
import os
import sys

from homeassistant.const import EntityCategory, Platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..common.consts import (
    CONFIG_FAN_MODES,
    CONFIG_HVAC_MODES,
    CONFIG_HVAC_SET,
    DEVICE_CODE,
    DEVICE_PRODUCT_ID,
    PRODUCT_ID_DEFAULT,
    PRODUCT_IDS,
    ProductParameter,
)
from ..common.entity_descriptions import (
    DEFAULT_ENTITY_DESCRIPTIONS,
    AquaTempBinarySensorEntityDescription,
    AquaTempEntityDescription,
    AquaTempSensorEntityDescription,
)

_LOGGER = logging.getLogger(__name__)


class ProductConfigurationManager:
    _entity_descriptions: dict
    _protocol_codes: dict
    _protocol_codes_configuration: dict
    platforms: list[str]

    def __init__(self):
        self._entity_descriptions = {}
        self._protocol_codes = {}
        self._protocol_codes_configuration = {}
        self.platforms = []

        self._hvac_modes = {}
        self._hvac_modes_reverse = {}

        self._fan_modes = {}
        self._fan_modes_reverse = {}

        self._devices = {}

    def initialize(self):
        try:
            self._load_entity_descriptions("default")
            self._load_protocol_codes("default")

            for product_id in PRODUCT_IDS:
                self._load_entity_descriptions(product_id)
                self._load_protocol_codes(product_id)

            _LOGGER.debug(
                f"Initialized Entity Descriptions: {len(self._entity_descriptions)}"
            )
            _LOGGER.debug(f"Initialized protocol codes: {self._protocol_codes}")
            _LOGGER.debug(
                f"Initialized protocol codes configuration: {self._protocol_codes_configuration}"
            )
            _LOGGER.debug(f"Initialized platforms: {self.platforms}")
            _LOGGER.debug(f"Initialized HVAC modes: {self._hvac_modes}")
            _LOGGER.debug(
                f"Initialized HVAC modes - reversed: {self._hvac_modes_reverse}"
            )
            _LOGGER.debug(f"Initialized Entity Descriptions: {self._fan_modes}")
            _LOGGER.debug(
                f"Initialized fan modes - reversed: {self._fan_modes_reverse}"
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to initialize, Error: {ex}, Line: {line_number}")

    def set_device(self, device_data: dict):
        device_code = device_data.get(DEVICE_CODE)
        product_id = device_data.get(DEVICE_PRODUCT_ID)

        config = self._protocol_codes_configuration.get(product_id)
        entity_descriptions = self._entity_descriptions.get(product_id)

        config_key = "default" if config is None else product_id
        entity_descriptions_key = (
            "default" if entity_descriptions is None else product_id
        )

        self._devices[device_code] = {
            ProductParameter.CONFIG: config_key,
            ProductParameter.ENTITY_DESCRIPTION: entity_descriptions_key,
        }

        _LOGGER.info(
            f"Device {device_code} mapped to "
            f"Product ID {product_id}, "
            f"Configuration: {config_key}, "
            f"Parameters: {entity_descriptions_key}"
        )

    def get_supported_protocol_codes(self, device_code) -> list[str]:
        product_id = self._get_product_id(device_code, ProductParameter.CONFIG)
        result = self._protocol_codes.get(product_id)

        return result

    def get_pc_key(self, device_code: str, key: str):
        config = self._get_pc_configuration(device_code)
        protocol_code_key = config.get(key)

        return protocol_code_key

    def get_hvac_mode_pc_key(self, device_code: str, hvac_mode: str, key: str):
        config = self._get_pc_configuration(device_code)

        hvac_modes = config.get(CONFIG_HVAC_MODES)
        hvac_mode_config = hvac_modes.get(hvac_mode)
        protocol_code_key = hvac_mode_config.get(key)

        return protocol_code_key

    def get_hvac_modes(self, device_code: str) -> list[str]:
        product_id = self._get_product_id(device_code, ProductParameter.CONFIG)

        result = self._hvac_modes.get(product_id)

        return result

    def get_fan_modes(self, device_code: str) -> list[str]:
        product_id = self._get_product_id(device_code, ProductParameter.CONFIG)

        result = self._fan_modes.get(product_id)

        return result

    def get_fan_reverse_mapping(self, device_code, fan_mode) -> str:
        product_id = self._get_product_id(device_code, ProductParameter.CONFIG)

        fan_modes = self._fan_modes_reverse.get(product_id)
        result = fan_modes.get(fan_mode)

        return result

    def get_hvac_reverse_mapping(self, device_code, hvac_mode) -> str:
        product_id = self._get_product_id(device_code, ProductParameter.CONFIG)

        hvac_modes = self._hvac_modes_reverse.get(product_id)
        result = hvac_modes.get(hvac_mode)

        return result

    def async_handle_discovered_device(
        self,
        device_code: str,
        coordinator,
        platform: Platform,
        entity_initializer,
        async_add_entities: AddEntitiesCallback,
    ):
        try:
            entities = []

            entity_descriptions = self._get_entity_descriptions(device_code)

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

    def find_entity_description(self, device_code: str, key: str, platform: Platform):
        entity_descriptions = self._get_entity_descriptions(device_code)

        entity_descriptions = [
            entity_description
            for entity_description in entity_descriptions
            if entity_description.platform == platform and entity_description.key == key
        ]

        result = None if len(entity_descriptions) == 0 else entity_descriptions[0]

        return result

    def _load_entity_descriptions(self, product_id: str):
        entities = copy(DEFAULT_ENTITY_DESCRIPTIONS)
        file_path = os.path.join(
            os.path.dirname(__file__), f"../parameters/{product_id}.json"
        )

        if not os.path.exists(file_path):
            return

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

                else:
                    entity = AquaTempEntityDescription(
                        key=data_item.get("key"), name=data_item.get("name")
                    )

                    entities.append(entity)

        self._update_platforms(entities)
        self._update_protocol_codes(product_id, entities)

        self._entity_descriptions[product_id] = entities

    def _load_protocol_codes(self, product_id: str):
        file_path = os.path.join(
            os.path.dirname(__file__), f"../parameters/{product_id}.config.json"
        )

        if not os.path.exists(file_path):
            return

        hvac_mode_mapping = {}
        hvac_mode_reverse_mapping = {}

        fan_mode_mapping = {}
        fan_mode_reverse_mapping = {}

        with open(file_path) as file:
            json_str = file.read()

            json_data = json.loads(json_str)

            self._protocol_codes_configuration[product_id] = json_data

            hvac_modes = json_data.get(CONFIG_HVAC_MODES)

            for hvac_mode_ha_key in hvac_modes:
                hvac_mode = hvac_modes[hvac_mode_ha_key]
                hvac_mode_api = hvac_mode.get(CONFIG_HVAC_SET)

                hvac_mode_mapping[hvac_mode_ha_key] = hvac_mode_api
                hvac_mode_reverse_mapping[hvac_mode_api] = hvac_mode_ha_key

            fan_modes = json_data.get(CONFIG_FAN_MODES)

            for fan_mode_ha in fan_modes:
                fan_mode = fan_modes[fan_mode_ha]

                fan_mode_mapping[fan_mode_ha] = fan_mode
                fan_mode_reverse_mapping[fan_mode] = fan_mode_ha

            self._hvac_modes[product_id] = hvac_mode_mapping
            self._hvac_modes_reverse[product_id] = hvac_mode_reverse_mapping

            self._fan_modes[product_id] = fan_mode_mapping
            self._fan_modes_reverse[product_id] = fan_mode_reverse_mapping

    def _update_platforms(self, entity_descriptions):
        for entity_description in entity_descriptions:
            if (
                entity_description.platform not in self.platforms
                and entity_description.platform is not None
            ):
                self.platforms.append(entity_description.platform)

    def _update_protocol_codes(self, product_id, entity_descriptions):
        self._protocol_codes[product_id] = [
            entity_description.key
            for entity_description in entity_descriptions
            if entity_description.is_protocol_code
        ]

    def _get_product_id(self, device_code: str, param: ProductParameter):
        device = self._devices.get(device_code, {})
        product_id = device.get(param)

        return product_id

    def _get_pc_configuration(self, device_code) -> dict:
        product_id = self._get_product_id(device_code, ProductParameter.CONFIG)

        result = self._protocol_codes_configuration.get(product_id)

        if result is None:
            result = self._protocol_codes_configuration.get(PRODUCT_ID_DEFAULT)

        return result

    def _get_entity_descriptions(self, device_code):
        product_id = self._get_product_id(
            device_code, ProductParameter.ENTITY_DESCRIPTION
        )

        result = self._entity_descriptions.get(product_id)

        if result is None:
            result = self._entity_descriptions.get(PRODUCT_ID_DEFAULT)

        return result
