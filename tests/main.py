import asyncio
import logging
import os
import sys

from custom_components.aqua_temp.managers.aqua_temp_api import AquaTempAPI
from custom_components.aqua_temp.managers.aqua_temp_config_manager import (
    AquaTempConfigManager,
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
        config_manager = AquaTempConfigManager(None, None)
        config_manager.update_credentials("elad.bar@hotmail.com", "Amit0807!")
        self._api = AquaTempAPI(None, config_manager)

    async def initialize(self):
        await self._api.initialize()

        for i in range(1, 10):
            await self._api.update()

            _LOGGER.info(self._api.data)

            await asyncio.sleep(30)


loop = asyncio.new_event_loop()

instance = Test()

try:
    loop.run_until_complete(instance.initialize())

except KeyboardInterrupt:
    _LOGGER.info("Aborted")

except Exception as rex:
    _LOGGER.error(f"Error: {rex}")
