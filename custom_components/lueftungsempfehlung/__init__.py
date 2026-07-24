from __future__ import annotations

from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CRITICAL_INDOOR_HUMIDITY,
    CONF_HUMIDITY_HYSTERESIS,
    CONF_HUMIDITY_SPIKE_THRESHOLD,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MAX_INDOOR_DEW_POINT_SPREAD,
    CONF_MAX_INDOOR_HUMIDITY,
    CONF_MAX_INDOOR_TEMPERATURE,
    CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
    CONF_MIN_INDOOR_TEMPERATURE,
    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
    CONF_MIN_INDOOR_HUMIDITY,
    CONF_MIN_TEMPERATURE_DELTA,
    CONF_NAME,
    CONF_NOTIFY_DEVICES,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_REMINDER_INTERVAL_MINUTES,
    CONF_REMINDER_MAX_COUNT,
    CONF_REQUIRE_OUTSIDE_COOLER,
    CONF_TEMPERATURE_HYSTERESIS,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_WINDOW_ENTITY,
    DEFAULT_HUMIDITY_HYSTERESIS,
    DEFAULT_CRITICAL_INDOOR_HUMIDITY,
    DEFAULT_HUMIDITY_SPIKE_THRESHOLD,
    DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
    DEFAULT_MAX_INDOOR_DEW_POINT_SPREAD,
    DEFAULT_MAX_INDOOR_HUMIDITY,
    DEFAULT_MAX_INDOOR_TEMPERATURE,
    DEFAULT_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
    DEFAULT_MIN_INDOOR_TEMPERATURE,
    DEFAULT_MIN_INDOOR_HUMIDITY,
    DEFAULT_MIN_TEMPERATURE_DELTA,
    DEFAULT_NAME,
    DEFAULT_REMINDER_INTERVAL_MINUTES,
    DEFAULT_REMINDER_MAX_COUNT,
    DEFAULT_REQUIRE_OUTSIDE_COOLER,
    DEFAULT_TEMPERATURE_HYSTERESIS,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import VentilationRecommendationCoordinator

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Required(CONF_INDOOR_TEMPERATURE_ENTITY): cv.entity_id,
                vol.Required(CONF_INDOOR_HUMIDITY_ENTITY): cv.entity_id,
                vol.Required(CONF_OUTDOOR_TEMPERATURE_ENTITY): cv.entity_id,
                vol.Required(CONF_OUTDOOR_HUMIDITY_ENTITY): cv.entity_id,
                vol.Optional(CONF_WINDOW_ENTITY): cv.entity_id,
                vol.Optional(CONF_NOTIFY_DEVICES, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(
                    CONF_REMINDER_INTERVAL_MINUTES,
                    default=DEFAULT_REMINDER_INTERVAL_MINUTES,
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                vol.Optional(
                    CONF_REMINDER_MAX_COUNT,
                    default=DEFAULT_REMINDER_MAX_COUNT,
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional(
                    CONF_REQUIRE_OUTSIDE_COOLER,
                    default=DEFAULT_REQUIRE_OUTSIDE_COOLER,
                ): cv.boolean,
                vol.Optional(
                    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
                    default=DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MAX_INDOOR_HUMIDITY,
                    default=DEFAULT_MAX_INDOOR_HUMIDITY,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CRITICAL_INDOOR_HUMIDITY,
                    default=DEFAULT_CRITICAL_INDOOR_HUMIDITY,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MIN_INDOOR_HUMIDITY,
                    default=DEFAULT_MIN_INDOOR_HUMIDITY,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MAX_INDOOR_TEMPERATURE,
                    default=DEFAULT_MAX_INDOOR_TEMPERATURE,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MIN_INDOOR_TEMPERATURE,
                    default=DEFAULT_MIN_INDOOR_TEMPERATURE,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MAX_INDOOR_DEW_POINT_SPREAD,
                    default=DEFAULT_MAX_INDOOR_DEW_POINT_SPREAD,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MIN_TEMPERATURE_DELTA,
                    default=DEFAULT_MIN_TEMPERATURE_DELTA,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_HUMIDITY_SPIKE_THRESHOLD,
                    default=DEFAULT_HUMIDITY_SPIKE_THRESHOLD,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_HUMIDITY_HYSTERESIS,
                    default=DEFAULT_HUMIDITY_HYSTERESIS,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_TEMPERATURE_HYSTERESIS,
                    default=DEFAULT_TEMPERATURE_HYSTERESIS,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_UPDATE_INTERVAL_MINUTES,
                    default=DEFAULT_UPDATE_INTERVAL_MINUTES,
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                vol.Optional(
                    CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
                    default=DEFAULT_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})

    if domain_config := config.get(DOMAIN):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=domain_config,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = VentilationRecommendationCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    coordinator.initialize_notification_tracking()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _handle_coordinator_update() -> None:
        hass.async_create_task(coordinator.async_send_notification_if_needed())

    entry.async_on_unload(coordinator.async_add_listener(_handle_coordinator_update))

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)