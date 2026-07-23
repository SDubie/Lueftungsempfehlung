from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_HUMIDITY_HYSTERESIS,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MAX_INDOOR_HUMIDITY,
    CONF_MAX_INDOOR_TEMPERATURE,
    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
    CONF_MIN_INDOOR_HUMIDITY,
    CONF_MIN_TEMPERATURE_DELTA,
    CONF_NAME,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_REQUIRE_OUTSIDE_COOLER,
    CONF_TEMPERATURE_HYSTERESIS,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_WINDOW_ENTITY,
    DEFAULT_HUMIDITY_HYSTERESIS,
    DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
    DEFAULT_MAX_INDOOR_HUMIDITY,
    DEFAULT_MAX_INDOOR_TEMPERATURE,
    DEFAULT_MIN_INDOOR_HUMIDITY,
    DEFAULT_MIN_TEMPERATURE_DELTA,
    DEFAULT_NAME,
    DEFAULT_REQUIRE_OUTSIDE_COOLER,
    DEFAULT_TEMPERATURE_HYSTERESIS,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)


def _build_unique_id(data: Mapping[str, Any]) -> str:
    return "|".join(
        [
            data[CONF_INDOOR_TEMPERATURE_ENTITY],
            data[CONF_INDOOR_HUMIDITY_ENTITY],
            data[CONF_OUTDOOR_TEMPERATURE_ENTITY],
            data[CONF_OUTDOOR_HUMIDITY_ENTITY],
        ]
    )


def _build_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    values = defaults or {}

    return vol.Schema(
        {
            vol.Optional(CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_INDOOR_TEMPERATURE_ENTITY,
                default=values.get(CONF_INDOOR_TEMPERATURE_ENTITY, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_INDOOR_HUMIDITY_ENTITY,
                default=values.get(CONF_INDOOR_HUMIDITY_ENTITY, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_OUTDOOR_TEMPERATURE_ENTITY,
                default=values.get(CONF_OUTDOOR_TEMPERATURE_ENTITY, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_OUTDOOR_HUMIDITY_ENTITY,
                default=values.get(CONF_OUTDOOR_HUMIDITY_ENTITY, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(
                CONF_WINDOW_ENTITY,
                default=values.get(CONF_WINDOW_ENTITY, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Optional(
                CONF_REQUIRE_OUTSIDE_COOLER,
                default=values.get(
                    CONF_REQUIRE_OUTSIDE_COOLER,
                    DEFAULT_REQUIRE_OUTSIDE_COOLER,
                ),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
                default=values.get(
                    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
                    DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1)
            ),
            vol.Optional(
                CONF_MAX_INDOOR_HUMIDITY,
                default=values.get(
                    CONF_MAX_INDOOR_HUMIDITY,
                    DEFAULT_MAX_INDOOR_HUMIDITY,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=30, max=90, step=1)
            ),
            vol.Optional(
                CONF_MIN_INDOOR_HUMIDITY,
                default=values.get(
                    CONF_MIN_INDOOR_HUMIDITY,
                    DEFAULT_MIN_INDOOR_HUMIDITY,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=60, step=1)
            ),
            vol.Optional(
                CONF_MAX_INDOOR_TEMPERATURE,
                default=values.get(
                    CONF_MAX_INDOOR_TEMPERATURE,
                    DEFAULT_MAX_INDOOR_TEMPERATURE,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=35, step=0.5)
            ),
            vol.Optional(
                CONF_MIN_TEMPERATURE_DELTA,
                default=values.get(
                    CONF_MIN_TEMPERATURE_DELTA,
                    DEFAULT_MIN_TEMPERATURE_DELTA,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=15, step=0.5)
            ),
            vol.Optional(
                CONF_HUMIDITY_HYSTERESIS,
                default=values.get(
                    CONF_HUMIDITY_HYSTERESIS,
                    DEFAULT_HUMIDITY_HYSTERESIS,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=5, step=0.1)
            ),
            vol.Optional(
                CONF_TEMPERATURE_HYSTERESIS,
                default=values.get(
                    CONF_TEMPERATURE_HYSTERESIS,
                    DEFAULT_TEMPERATURE_HYSTERESIS,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=5, step=0.1)
            ),
            vol.Optional(
                CONF_UPDATE_INTERVAL_MINUTES,
                default=values.get(
                    CONF_UPDATE_INTERVAL_MINUTES,
                    DEFAULT_UPDATE_INTERVAL_MINUTES,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=60, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


class LueftungsempfehlungConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(_build_unique_id(user_input))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
            )

        return self.async_show_form(step_id="user", data_schema=_build_schema())

    async def async_step_import(self, user_input: dict[str, Any]):
        await self.async_set_unique_id(_build_unique_id(user_input))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input.get(CONF_NAME, DEFAULT_NAME),
            data=user_input,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return LueftungsempfehlungOptionsFlow(config_entry)


class LueftungsempfehlungOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_build_schema(defaults))