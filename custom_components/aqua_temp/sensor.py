from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TEMPERATURE_UNIT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .aqua_temp_coordinator import AquaTempCoordinator
from .consts import DEFAULT_TEMPERATURE_UNIT, DOMAIN, PROTOCOL_CODES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Setup the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    temperature_entities = [
        AquaTempTemperatureEntity(coordinator, key)
        for key in PROTOCOL_CODES
        if key.startswith("T") and PROTOCOL_CODES.get(key) is not None
    ]

    async_add_entities(temperature_entities)


class AquaTempTemperatureEntity(CoordinatorEntity):
    """Representation of a sensor."""

    def __init__(self, device_code: str, key: str, coordinator: AquaTempCoordinator):
        super().__init__(coordinator)
        self._key = key
        self._device_code = device_code

    @property
    def _api_data(self):
        return self.coordinator.api_data[self._device_code]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self.coordinator.config_data.get(
            CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        device_nickname = self._api_data.get("device_nick_name", self._device_code)

        return (
            f"{self.coordinator.name} {device_nickname} {PROTOCOL_CODES.get(self._key)}"
        )

    def entity_id(self):
        slugify_name = slugify(self.name)
        return f"sensor.{slugify_name}"

    @property
    def unique_id(self):
        """Return the device code of the sensor as a unique ID to allow the devices to be edited on the dashboard."""
        device_id = self._api_data.get("device_id")
        slugify_uid = slugify(f"sensor_{self._key}_{device_id}")

        return slugify_uid

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.api_data is None:
            value_str = None

        else:
            value_str = self._api_data.get(self._key)

        value = 0 if value_str is None else float(value_str)

        return value
