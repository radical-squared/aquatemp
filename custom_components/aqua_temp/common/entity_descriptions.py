from dataclasses import dataclass

from custom_components.aqua_temp.common.consts import API_STATUS, POWER_MODE_ON
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.components.climate import ClimateEntityDescription, HVACMode
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import EntityCategory, Platform, UnitOfTemperature
from homeassistant.helpers.entity import EntityDescription


@dataclass(slots=True)
class AquaTempEntityDescription(EntityDescription):
    platform: Platform | None = None
    is_protocol_code: bool = True


@dataclass(slots=True)
class AquaTempClimateEntityDescription(
    ClimateEntityDescription, AquaTempEntityDescription
):
    platform: Platform | None = Platform.CLIMATE
    fan_modes: list[str] | None = None
    hvac_modes: list[HVACMode] | list[str] = None


@dataclass(slots=True)
class AquaTempBinarySensorEntityDescription(
    BinarySensorEntityDescription, AquaTempEntityDescription
):
    platform: Platform | None = Platform.BINARY_SENSOR
    on_value: str | bool | None = None
    attributes: list[str] | None = None


@dataclass(slots=True)
class AquaTempSensorEntityDescription(
    SensorEntityDescription, AquaTempEntityDescription
):
    platform: Platform | None = Platform.SENSOR


@dataclass(slots=True)
class AquaTempSelectEntityDescription(
    SelectEntityDescription, AquaTempEntityDescription
):
    platform: Platform | None = Platform.SELECT


DEFAULT_ENTITY_DESCRIPTIONS: list[AquaTempEntityDescription] = [
    AquaTempBinarySensorEntityDescription(
        key=API_STATUS,
        name="API Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        on_value=True,
        translation_key=API_STATUS,
    ),
    AquaTempSelectEntityDescription(
        key="temperature_unit",
        name="Temperature Unit",
        options=[UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT],
        entity_category=EntityCategory.CONFIG,
        is_protocol_code=False,
        translation_key="temperature_unit",
    ),
    AquaTempBinarySensorEntityDescription(
        key="is_fault",
        name="Fault",
        on_value=POWER_MODE_ON,
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.PROBLEM,
        attributes=["fault"],
        translation_key="is_fault",
    ),
    AquaTempBinarySensorEntityDescription(
        key="device_status",
        name="Status",
        on_value="ONLINE",
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        translation_key="device_status",
    ),
    AquaTempClimateEntityDescription(key="Mode", translation_key="mode"),
]
