from homeassistant.config_entries import STORAGE_VERSION, ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ..common.consts import (
    CONF_TEMPERATURE_UNIT,
    CONFIG_FIELDS,
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
)


class AquaTempConfigManager:
    def __init__(self, hass: HomeAssistant | None, entry: ConfigEntry | None):
        self._hass = hass
        self._entry = entry
        self.data = {}

        if entry is not None:
            file_name = f"{DOMAIN}.{entry.entry_id}.config.json"

            self._store = Store(hass, STORAGE_VERSION, file_name, encoder=JSONEncoder)

    @property
    def name(self):
        return self._entry.title

    @property
    def unique_id(self):
        return self._entry.unique_id

    async def initialize(self):
        local_data = await self._load()

        self.data[CONF_USERNAME] = self._entry.data.get(CONF_USERNAME)
        self.data[CONF_PASSWORD] = self._entry.data.get(CONF_PASSWORD)

        for key in local_data:
            value = local_data[key]

            self.data[key] = value

    def update_credentials(self, username, password):
        self.data[CONF_USERNAME] = username
        self.data[CONF_PASSWORD] = password

    async def update_temperature_unit(self, value):
        self.data[CONF_TEMPERATURE_UNIT] = value

    async def _load(self):
        result = await self._store.async_load()

        if result is None:
            result = {
                CONF_TEMPERATURE_UNIT: DEFAULT_TEMPERATURE_UNIT,
            }

        return result

    async def _save(self):
        data = {}
        for key in CONFIG_FIELDS:
            data[key] = self.data[key]

        await self._store.async_save(self.data)
