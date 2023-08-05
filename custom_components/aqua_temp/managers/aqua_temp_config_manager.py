from copy import copy
import json
import logging
import os

from homeassistant.config_entries import STORAGE_VERSION, ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_TEMPERATURE_UNIT,
    CONF_USERNAME,
    EntityCategory,
    Platform,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ..common.api_types import APIParam
from ..common.consts import (
    CONFIG_FAN_MODES,
    CONFIG_HVAC_MODES,
    CONFIG_HVAC_SET,
    CONFIGURATION_FILE,
    DEFAULT_ENTRY_ID,
    DEFAULT_NAME,
    DOMAIN,
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
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class AquaTempConfigManager:
    _api_config: dict | None
    _translations: dict | None
    _entry: ConfigEntry | None
    _entry_id: str
    _entry_title: str
    _config_data: ConfigData

    def __init__(self, hass: HomeAssistant | None, entry: ConfigEntry | None):
        self._hass = hass

        self._data = None
        self.platforms = []

        self._entity_descriptions = {}
        self._protocol_codes = {}
        self._protocol_codes_configuration = {}

        self._hvac_modes = {}
        self._hvac_modes_reverse = {}

        self._fan_modes = {}
        self._fan_modes_reverse = {}

        self._devices = {}
        self._api_config = None
        self._translations = None

        self._entry = entry
        self._entry_id = DEFAULT_ENTRY_ID if entry is None else entry.entry_id
        self._entry_title = DEFAULT_NAME if entry is None else entry.title

        self._config_data = ConfigData()

        self._is_initialized = False

        if hass is not None:
            self._store = Store(
                hass, STORAGE_VERSION, CONFIGURATION_FILE, encoder=JSONEncoder
            )

    @property
    def is_initialized(self) -> bool:
        is_initialized = self._is_initialized

        return is_initialized

    @property
    def entry_id(self) -> str:
        entry_id = self._entry_id

        return entry_id

    @property
    def entry_title(self) -> str:
        entry_title = self._entry_title

        return entry_title

    @property
    def entry(self) -> ConfigEntry:
        entry = self._entry

        return entry

    @property
    def config_data(self) -> ConfigData:
        config_data = self._config_data

        return config_data

    async def initialize(self, entry_config: dict):
        await self._load()

        self._config_data.update(entry_config)

        self._load_api_config()

        self._translations = await translation.async_get_translations(
            self._hass, self._hass.config.language, "entity", {DOMAIN}
        )

        self._is_initialized = True

    async def remove(self, entry_id: str):
        if self._store is None:
            return

        store_data = await self._store.async_load()

        entries = [DEFAULT_ENTRY_ID, entry_id]

        if store_data is not None:
            should_save = False
            data = {key: store_data[key] for key in store_data}

            for rm_entry_id in entries:
                if rm_entry_id in store_data:
                    data.pop(rm_entry_id)

                    should_save = True

            if should_save:
                await self._store.async_save(data)

    def get_entity_name(
        self, entity_description: AquaTempEntityDescription, device_info: DeviceInfo
    ) -> str:
        entity_key = entity_description.key
        platform = entity_description.platform

        device_name = device_info.get("name")

        translation_key = f"component.{DOMAIN}.entity.{platform}.{entity_key}.name"

        translated_name = self._translations.get(
            translation_key, entity_description.name
        )

        _LOGGER.debug(
            f"Translations requested, Key: {translation_key}, "
            f"Entity: {entity_description.name}, Value: {translated_name}"
        )

        entity_name = (
            device_name
            if translated_name is None or translated_name == ""
            else f"{device_name} {translated_name}"
        )

        return entity_name

    async def update_temperature_unit(self, device_code: str, value: str):
        _LOGGER.debug(f"Set temperature unit for device '{device_code}' to {value}")

        self._data[CONF_TEMPERATURE_UNIT][device_code] = value

        await self._save()

    def set_device(self, device_code: str, product_id: str):
        config = self._protocol_codes_configuration.get(product_id)
        entity_descriptions = self._entity_descriptions.get(product_id)

        mapping_key = "default" if config is None else product_id
        entity_descriptions_key = (
            "default" if entity_descriptions is None else product_id
        )

        self._devices[device_code] = {
            ProductParameter.MAPPING: mapping_key,
            ProductParameter.ENTITY_DESCRIPTION: entity_descriptions_key,
        }

        _LOGGER.info(
            f"Device {device_code} mapped to "
            f"Product ID {product_id}, "
            f"Mapping Key: {mapping_key}, "
            f"Entity Description Key: {entity_descriptions_key}"
        )

    def get_temperature_unit(self, device_code: str):
        temperature_units = self._data.get(CONF_TEMPERATURE_UNIT, {})
        temperature_unit = temperature_units.get(device_code, UnitOfTemperature.CELSIUS)

        return temperature_unit

    def get_supported_protocol_codes(self, device_code) -> list[str]:
        product_id = self._get_product_id(
            device_code, ProductParameter.ENTITY_DESCRIPTION
        )
        result = self._protocol_codes.get(product_id)

        return result

    def get_pc_key(self, device_code: str, key: str):
        config = self._get_pc_mapping(device_code)
        protocol_code_key = config.get(key)

        return protocol_code_key

    def get_hvac_mode_pc_key(self, device_code: str, hvac_mode: str, key: str):
        config = self._get_pc_mapping(device_code)

        hvac_modes = config.get(CONFIG_HVAC_MODES)
        hvac_mode_config = hvac_modes.get(hvac_mode)
        protocol_code_key = hvac_mode_config.get(key)

        return protocol_code_key

    def get_hvac_modes(self, device_code: str) -> list[str]:
        product_id = self._get_product_id(device_code, ProductParameter.MAPPING)

        result = self._hvac_modes.get(product_id)

        return result

    def get_fan_modes(self, device_code: str) -> list[str]:
        product_id = self._get_product_id(device_code, ProductParameter.MAPPING)

        result = self._fan_modes.get(product_id)

        return result

    def get_fan_reverse_mapping(self, device_code, fan_mode) -> str:
        product_id = self._get_product_id(device_code, ProductParameter.MAPPING)

        fan_modes = self._fan_modes_reverse.get(product_id)
        result = fan_modes.get(fan_mode)

        return result

    def get_hvac_reverse_mapping(self, device_code, hvac_mode) -> str:
        product_id = self._get_product_id(device_code, ProductParameter.MAPPING)

        hvac_modes = self._hvac_modes_reverse.get(product_id)
        result = hvac_modes.get(hvac_mode)

        return result

    def get_api_param(self, param: APIParam):
        result = self._api_config.get(str(param))

        return result

    def get_debug_data(self) -> dict:
        data = self._config_data.to_dict()

        for key in self._data:
            data[key] = self._data[key]

        return data

    async def _load(self):
        self._data = None

        await self._load_config_from_file()

        if self._data is None:
            self._data = {}

        default_configuration = self._get_defaults()

        for key in default_configuration:
            value = default_configuration[key]

            if key not in self._data:
                self._data[key] = value

        await self._save()

        self._load_entity_descriptions("default")
        self._load_pc_mapping("default")

        for product_id in PRODUCT_IDS:
            self._load_entity_descriptions(product_id)
            self._load_pc_mapping(product_id)

        log_messages = [
            f"Entity Descriptions: {len(self._entity_descriptions)}",
            f"protocol codes: {len(self._protocol_codes)}",
            f"protocol codes configuration: {len(self._protocol_codes_configuration)}",
            f"platforms: {len(self.platforms)}",
            f"HVAC modes: {self._hvac_modes}",
            f"HVAC modes - reversed: {self._hvac_modes_reverse}",
            f"Fan modes: {self._fan_modes}",
            f"Fan modes - reversed: {self._fan_modes_reverse}",
        ]

        log_message = f"Initialized, {', '.join(log_messages)}"

        _LOGGER.debug(log_message)

    async def _load_config_from_file(self):
        if self._store is not None:
            store_data = await self._store.async_load()

            if store_data is not None:
                self._data = store_data.get(self._entry_id)

    @staticmethod
    def _get_defaults() -> dict:
        data = {CONF_TEMPERATURE_UNIT: {}}

        return data

    async def _save(self):
        if self._store is None:
            return

        should_save = False
        store_data = await self._store.async_load()

        if store_data is None:
            store_data = {}

        entry_data = store_data.get(self._entry_id, {})

        _LOGGER.debug(
            f"Storing config data: {json.dumps(self._data)}, "
            f"Exiting: {json.dumps(entry_data)}"
        )

        for key in self._data:
            stored_value = entry_data.get(key)

            if key in [CONF_PASSWORD, CONF_USERNAME]:
                entry_data.pop(key)

                if stored_value is not None:
                    should_save = True

            else:
                current_value = self._data.get(key)

                if stored_value != current_value:
                    should_save = True

                    entry_data[key] = self._data[key]

        if DEFAULT_ENTRY_ID in store_data:
            store_data.pop(DEFAULT_ENTRY_ID)
            should_save = True

        if should_save:
            store_data[self._entry_id] = entry_data

            await self._store.async_save(store_data)

    def _load_entity_descriptions(self, product_id: str):
        entities = copy(DEFAULT_ENTITY_DESCRIPTIONS)
        file_path = self._get_product_file(
            ProductParameter.ENTITY_DESCRIPTION, product_id
        )

        if not os.path.exists(file_path):
            return

        with open(file_path) as file:
            json_str = file.read()

            json_data = json.loads(json_str)

            for data_item in json_data:
                platform = data_item.get("platform")
                key = data_item.get("key")
                translation_key = f"{product_id}_{key}".replace("/", "").lower()

                if platform == Platform.SENSOR:
                    sensor_entity = AquaTempSensorEntityDescription(
                        key=key,
                        name=data_item.get("name"),
                        device_class=data_item.get("device_class"),
                        native_unit_of_measurement=data_item.get("unit_of_measurement"),
                        entity_category=EntityCategory.DIAGNOSTIC,
                        translation_key=translation_key,
                    )

                    entities.append(sensor_entity)

                elif platform == Platform.BINARY_SENSOR:
                    binary_sensor_entity = AquaTempBinarySensorEntityDescription(
                        key=key,
                        name=data_item.get("name"),
                        device_class=data_item.get("device_class"),
                        on_value=data_item.get("on_value"),
                        entity_category=EntityCategory.DIAGNOSTIC,
                        translation_key=translation_key,
                    )

                    entities.append(binary_sensor_entity)

                else:
                    entity = AquaTempEntityDescription(
                        key=key, name=data_item.get("name")
                    )

                    entities.append(entity)

        self._update_platforms(entities)
        self._update_protocol_codes(product_id, entities)

        self._entity_descriptions[product_id] = entities

    def _load_pc_mapping(self, product_id: str):
        file_path = self._get_product_file(ProductParameter.MAPPING, product_id)

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

    def _load_api_config(self):
        api_type = self._config_data.api_type
        config_file = f"../parameters/api.{api_type}.json"
        file_path = os.path.join(os.path.dirname(__file__), config_file)

        if not os.path.exists(file_path):
            return

        with open(file_path) as file:
            json_str = file.read()

            json_data = json.loads(json_str)

            self._api_config = json_data

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

    def _get_pc_mapping(self, device_code) -> dict:
        product_id = self._get_product_id(device_code, ProductParameter.MAPPING)

        result = self._protocol_codes_configuration.get(product_id)

        if result is None:
            result = self._protocol_codes_configuration.get(PRODUCT_ID_DEFAULT)

        return result

    def get_entity_descriptions(self, device_code):
        product_id = self._get_product_id(
            device_code, ProductParameter.ENTITY_DESCRIPTION
        )

        result = self._entity_descriptions.get(product_id)

        if result is None:
            result = self._entity_descriptions.get(PRODUCT_ID_DEFAULT)

        return result

    @staticmethod
    def _get_product_file(parameter: ProductParameter, product_id):
        config_file = f"../parameters/{parameter}.{product_id}.json"
        file_path = os.path.join(os.path.dirname(__file__), config_file)

        return file_path
