"""Diagnostics support for Tuya."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .common.api_types import APIParam
from .common.consts import (
    DATA_ITEM_CONFIG,
    DATA_ITEM_DEVICES,
    DATA_ITEM_LOGIN_DETAILS,
    DOMAIN,
    TO_REDACT,
)
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Starting diagnostic tool")

    coordinator = hass.data[DOMAIN][entry.entry_id]

    return _async_get_diagnostics(hass, coordinator, entry)


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    return _async_get_diagnostics(hass, coordinator, entry, device)


@callback
def _async_get_diagnostics(
    hass: HomeAssistant,
    coordinator: AquaTempCoordinator,
    entry: ConfigEntry,
    device: DeviceEntry | None = None,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Getting diagnostic information")

    debug_data = async_redact_data(coordinator.get_debug_data(), TO_REDACT)

    devices = debug_data.get(DATA_ITEM_DEVICES)
    config_data = debug_data.get(DATA_ITEM_CONFIG)
    login_details = debug_data.get(DATA_ITEM_LOGIN_DETAILS)

    device_id_param = coordinator.config_manager.get_api_param(APIParam.DeviceId)

    data = {
        DATA_ITEM_LOGIN_DETAILS: login_details,
        DATA_ITEM_CONFIG: config_data,
        "disabled_by": entry.disabled_by,
        "disabled_polling": entry.pref_disable_polling,
    }

    if device is not None:
        device_id = next(iter(device.identifiers))[1]

        for device_code in devices:
            device_details = devices[device_code]
            if device_details.get(device_id_param) == device_id:
                data |= _async_device_as_dict(hass, device_details)

    else:
        _LOGGER.debug("Getting diagnostic information for all devices")

        data.update(
            devices=[
                _async_device_as_dict(
                    hass, devices[device_code][device_id_param], devices[device_code]
                )
                for device_code in devices
            ]
        )

    return data


@callback
def _async_device_as_dict(
    hass: HomeAssistant, device_id: str, device_data: dict
) -> dict[str, Any]:
    """Represent a Shinobi monitor as a dictionary."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    ha_device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    data = {}

    if ha_device:
        data["device"] = {
            "name": ha_device.name,
            "name_by_user": ha_device.name_by_user,
            "disabled": ha_device.disabled,
            "disabled_by": ha_device.disabled_by,
            "data": device_data,
            "entities": [],
        }

        ha_entities = er.async_entries_for_device(
            entity_registry,
            device_id=ha_device.id,
            include_disabled_entities=True,
        )

        for entity_entry in ha_entities:
            state = hass.states.get(entity_entry.entity_id)
            state_dict = None
            if state:
                state_dict = dict(state.as_dict())

                # The context doesn't provide useful information in this case.
                state_dict.pop("context", None)

            data["device"]["entities"].append(
                {
                    "disabled": entity_entry.disabled,
                    "disabled_by": entity_entry.disabled_by,
                    "entity_category": entity_entry.entity_category,
                    "device_class": entity_entry.device_class,
                    "original_device_class": entity_entry.original_device_class,
                    "icon": entity_entry.icon,
                    "original_icon": entity_entry.original_icon,
                    "unit_of_measurement": entity_entry.unit_of_measurement,
                    "state": state_dict,
                }
            )

    return data
