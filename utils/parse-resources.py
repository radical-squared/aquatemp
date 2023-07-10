from copy import copy
import json
import logging
import os
import sys

import xmltodict

from custom_components.aqua_temp.common.consts import ProductParameter
from utils.common.component_handlers import ComponentHandlers
from utils.common.consts import CUSTOM_PARAMETERS
from utils.devices.default.consts import PARAMETER_MAPPING as PARAMETER_MAPPING_DEFAULT
from utils.devices.device_1245226668902080512.consts import (
    PARAMETER_MAPPING as PARAMETER_MAPPING_1245226668902080512,
)
from utils.devices.device_1442284873216843776.consts import (
    PARAMETER_MAPPING as PARAMETER_MAPPING_DEFAULT_1442284873216843776,
)

DEBUG = str(os.environ.get("DEBUG", False)).lower() == str(True).lower()

log_level = logging.DEBUG if DEBUG else logging.INFO

root = logging.getLogger()
root.setLevel(log_level)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
stream_handler.setFormatter(formatter)
root.addHandler(stream_handler)

_LOGGER = logging.getLogger(__name__)


class Test:
    def __init__(self):
        self._component_handlers = ComponentHandlers()
        self._translation_keys = {}

        self._devices = {
            "default": PARAMETER_MAPPING_DEFAULT,
            "device_1245226668902080512": PARAMETER_MAPPING_1245226668902080512,
            "device_1442284873216843776": PARAMETER_MAPPING_DEFAULT_1442284873216843776
        }

    def initialize(self):
        for device in self._devices:
            parameter_mapping = self._devices[device]
            self.initialize_file(device, parameter_mapping)

        _LOGGER.info(json.dumps(self._translation_keys, indent=4))

    def initialize_file(self, device, parameter_mapping):
        try:
            device_name = device.replace("device_", "")
            xml_file_path = os.path.join(os.path.dirname(__file__), f'devices\\{device}\\resources.xml')

            json_file_key = f"{ProductParameter.ENTITY_DESCRIPTION}.{device_name}"

            json_file_path = os.path.join(
                os.path.dirname(__file__),
                f"..\\custom_components\\aqua_temp\\parameters\\{json_file_key}.json"
            )

            with open(xml_file_path, encoding="utf-8") as xml_file:
                xml = xmltodict.parse(xml_file.read())

                resources = xml.get("resources")
                items = resources.get("array")
                parameters = copy(CUSTOM_PARAMETERS)

                for item in items:
                    name = item.get("@name")
                    item_data = item.get("item")
                    config = parameter_mapping.get(name)

                    if config is not None:
                        category_parameters = self.parse_category(item_data, config)

                        parameters.extend(category_parameters)

                # with open(json_file_path, "w+") as json_file:
                #    json_file.write(json.dumps(parameters, indent=4))

                for parameter in parameters:
                    parameter_key = parameter.get("key")
                    parameter_name = parameter.get("name")

                    key = f"{device_name}_{parameter_key}".lower()
                    self._translation_keys[key] = {
                        "name": parameter_name
                    }

                _LOGGER.info(f"{device_name}: {parameters}")

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize file, Device: {device}, Error: {ex}, Line: {line_number}"
            )

    def parse_category(self, item_data, config):
        result = []

        parameter = config.get("name")
        skip_parameter = config.get("skip", [])
        bar_parameter = config.get("bar_parameter")
        rotation_parameter = config.get("rotation_parameter")

        index = 0
        parameter_index = 0

        leading_0 = config.get("leading_0", True)

        for item in item_data:
            suffix = ""

            if index in config.get("bar") and bar_parameter is not None:
                suffix = bar_parameter

            elif index in config.get("rotation") and rotation_parameter is not None:
                suffix = rotation_parameter

            else:
                parameter_index += 1

                while parameter_index in skip_parameter:
                    parameter_index += 1

            key_id = str(parameter_index)

            if leading_0:
                key_id = key_id.rjust(2, "0")

            key = f"{parameter}{key_id}{suffix}"

            data = self._component_handlers.get_description(index, key, item, config)

            result.append(data)

            index += 1

        return result


try:
    instance = Test()
    instance.initialize()


except KeyboardInterrupt:
    _LOGGER.info("Aborted")

except Exception as rex:
    _LOGGER.error(f"Error: {rex}")
