from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
    CONF_NAME,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_REQUIRE_OUTSIDE_COOLER,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
    DEFAULT_NAME,
    DEFAULT_REQUIRE_OUTSIDE_COOLER,
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
                vol.Optional(
                    CONF_REQUIRE_OUTSIDE_COOLER,
                    default=DEFAULT_REQUIRE_OUTSIDE_COOLER,
                ): cv.boolean,
                vol.Optional(
                    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
                    default=DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_UPDATE_INTERVAL_MINUTES,
                    default=DEFAULT_UPDATE_INTERVAL_MINUTES,
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
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

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)