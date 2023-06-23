import asyncio
import json
import logging
import os
import sys

from custom_components.aqua_temp import ProductConfigurationManager
from custom_components.aqua_temp.managers.aqua_temp_api import AquaTempAPI
from custom_components.aqua_temp.managers.aqua_temp_config_manager import (
    AquaTempConfigManager,
)

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
        self._product_config_manager = ProductConfigurationManager()

        config_manager = AquaTempConfigManager(None, None)
        config_manager.update_credentials(USERNAME, PASSWORD)
        self._api = AquaTempAPI(None, config_manager, self._product_config_manager)

    async def parameters_list(self):
        await self._api.initialize()

    async def list_data(self):
        await self._api.initialize()

        await self._api.update()

        for device_code in self._api.devices:
            device_data = self._api.get_device_data(device_code)

            _LOGGER.info(f"{device_code}: {json.dumps(device_data, indent=4)}")

        await self._api.terminate()

    @staticmethod
    async def entities_mapping():
        print("| Entity Name | Parameter | Platform | Protocol Code? |")
        print("| ----------- | --------- | -------- | -------------- |")

        for entity_description in []:
            if entity_description.platform is not None:
                print(
                    f"| {{HA Device Name}} "
                    f"{entity_description.name} | "
                    f"{entity_description.key} | "
                    f"{entity_description.platform} | "
                    f"{entity_description.is_protocol_code} |"
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
