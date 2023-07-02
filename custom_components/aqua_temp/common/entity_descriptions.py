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
    category: str | None = None
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


DEFAULT_ENTITY_DESCRIPTIONS: list[
    AquaTempEntityDescription
    | AquaTempSelectEntityDescription
    | AquaTempSensorEntityDescription
    | AquaTempBinarySensorEntityDescription
] = [
    AquaTempBinarySensorEntityDescription(
        key=API_STATUS,
        name="API Status",
        category="Status parameters",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    AquaTempSelectEntityDescription(
        key="temperature_unit",
        name="Temperature Unit",
        category="Status parameters",
        options=[UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT],
        entity_category=EntityCategory.CONFIG,
        is_protocol_code=False,
    ),
    AquaTempBinarySensorEntityDescription(
        key="is_fault",
        name="Fault",
        category="Status parameters",
        on_value=POWER_MODE_ON,
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.PROBLEM,
        attributes=["fault"],
    ),
    AquaTempBinarySensorEntityDescription(
        key="device_status",
        name="Status",
        category="Status parameters",
        on_value="ONLINE",
        is_protocol_code=False,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    AquaTempClimateEntityDescription(
        key="Mode", name="HVAC Mode", category="Control parameters"
    ),
]
