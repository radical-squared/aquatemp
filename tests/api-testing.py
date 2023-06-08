import asyncio
import logging
import os
import sys

from custom_components.aqua_temp.common.consts import PROTOCAL_CODES
from custom_components.aqua_temp.common.entity_descriptions import ALL_ENTITIES
from custom_components.aqua_temp.managers.aqua_temp_api import AquaTempAPI
from custom_components.aqua_temp.managers.aqua_temp_config_manager import (
    AquaTempConfigManager,
)
from homeassistant.const import Platform

DEBUG = str(os.environ.get("DEBUG", False)).lower() == str(True).lower()
USERNAME = os.environ.get("USERNAME", False)
PASSWORD = os.environ.get("PASSWORD", False)

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
        config_manager = AquaTempConfigManager(None, None)
        config_manager.update_credentials(USERNAME, PASSWORD)
        self._api = AquaTempAPI(None, config_manager)

    async def parameters_list(self):
        await self._api.initialize()

    async def list_data(self):
        await self._api.initialize()

        await self._api.update()

        print(f"| Parameter | Device Code | Value | Description           |")
        print(f"| --------- | ----------- | ----- | --------------------- |")

        for device_code in self._api.devices:
            device_data = self._api.get_device_data(device_code)
            device_entities = device_data.get(PROTOCAL_CODES)

            for entity_description in device_entities:
                value = device_data.get(entity_description.key)

                if entity_description.platform == Platform.BINARY_SENSOR:
                    value = value == entity_description.on_value

                if value is not None and value != "":
                    print(f"| {entity_description.key} | {device_code} | {value} | {entity_description.name} |")

        await self._api.terminate()

    @staticmethod
    async def protocol_code_mapping():
        protocol_categories = {}

        for entity_description in ALL_ENTITIES:
            if entity_description.is_protocol_code:
                if entity_description.category not in protocol_categories:
                    protocol_categories[entity_description.category] = []

                protocol_categories[entity_description.category].append(entity_description)

        for protocol_category in protocol_categories:
            entity_descriptions = protocol_categories[protocol_category]
            print(f"### {protocol_category}")

            print(f"| Parameter | Description           |")
            print(f"| --------- | --------------------- |")

            for entity_description in entity_descriptions:
                print(f"| {entity_description.key} | {entity_description.name} |")

    @staticmethod
    async def entities_mapping():
        print("| Entity Name | Parameter | Platform | Protocol Code? |")
        print("| ----------- | --------- | -------- | -------------- |")

        for entity_description in ALL_ENTITIES:
            if entity_description.platform is not None:
                print(
                    f"| {{HA Device Name}} "
                    f"{entity_description.name} | "
                    f"{entity_description.key} | "
                    f"{entity_description.platform} | "
                    f"{entity_description.is_protocol_code} |"
                )

    async def parameters_details(self):
        await self.parameters_list()

        await self._api.update()

        print(self._api.devices)

        for device_code in self._api.devices:
            device_data = self._api.devices[device_code]

            for entity_description in ALL_ENTITIES:
                value = device_data.get(entity_description.key)
                _LOGGER.debug(
                    f"{entity_description.key}::"
                    f"{entity_description.name} "
                    f"[{entity_description.category}] = "
                    f"{value}"
                )

    async def api_test(self):
        await self._api.initialize()

        for i in range(1, 10):
            await self._api.update()

            _LOGGER.info(self._api.devices)

            await asyncio.sleep(30)

    async def terminate(self):
        await self._api.terminate()


loop = asyncio.new_event_loop()

instance = Test()

try:
    loop.create_task(instance.list_data())
    loop.run_forever()


except KeyboardInterrupt:
    _LOGGER.info("Aborted")

except Exception as rex:
    _LOGGER.error(f"Error: {rex}")
