from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_CRITICAL_INDOOR_HUMIDITY,
    CONF_HUMIDITY_HYSTERESIS,
    CONF_HUMIDITY_SPIKE_THRESHOLD,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MAX_INDOOR_DEW_POINT_SPREAD,
    CONF_MAX_INDOOR_HUMIDITY,
    CONF_MAX_INDOOR_TEMPERATURE,
    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
    CONF_MIN_INDOOR_HUMIDITY,
    CONF_MIN_INDOOR_TEMPERATURE,
    CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
    CONF_MIN_TEMPERATURE_DELTA,
    CONF_NAME,
    CONF_NOTIFICATION_SILENCE_END,
    CONF_NOTIFICATION_SILENCE_ENTITY,
    CONF_NOTIFICATION_SILENCE_START,
    CONF_NOTIFY_DEVICES,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_REMINDER_INTERVAL_MINUTES,
    CONF_REMINDER_MAX_COUNT,
    CONF_REQUIRE_OUTSIDE_COOLER,
    CONF_TEMPERATURE_HYSTERESIS,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_WINDOW_ENTITY,
    DEFAULT_CRITICAL_INDOOR_HUMIDITY,
    DEFAULT_HUMIDITY_HYSTERESIS,
    DEFAULT_HUMIDITY_SPIKE_THRESHOLD,
    DEFAULT_MAX_INDOOR_DEW_POINT_SPREAD,
    DEFAULT_MAX_INDOOR_HUMIDITY,
    DEFAULT_MAX_INDOOR_TEMPERATURE,
    DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
    DEFAULT_MIN_INDOOR_HUMIDITY,
    DEFAULT_MIN_INDOOR_TEMPERATURE,
    DEFAULT_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
    DEFAULT_MIN_TEMPERATURE_DELTA,
    DEFAULT_NAME,
    DEFAULT_NOTIFICATION_SILENCE_END,
    DEFAULT_NOTIFICATION_SILENCE_ENTITY,
    DEFAULT_NOTIFICATION_SILENCE_START,
    DEFAULT_REMINDER_INTERVAL_MINUTES,
    DEFAULT_REMINDER_MAX_COUNT,
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


def _build_basic_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
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
        }
    )


def _build_notification_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    values = defaults or {}

    return vol.Schema(
        {
            vol.Optional(
                CONF_NOTIFY_DEVICES,
                default=values.get(CONF_NOTIFY_DEVICES, []),
            ): selector.DeviceSelector(
                selector.DeviceSelectorConfig(
                    integration="mobile_app",
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_REMINDER_INTERVAL_MINUTES,
                default=values.get(
                    CONF_REMINDER_INTERVAL_MINUTES,
                    DEFAULT_REMINDER_INTERVAL_MINUTES,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=1440, step=1)
            ),
            vol.Optional(
                CONF_REMINDER_MAX_COUNT,
                default=values.get(
                    CONF_REMINDER_MAX_COUNT,
                    DEFAULT_REMINDER_MAX_COUNT,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1)
            ),
            vol.Optional(
                CONF_NOTIFICATION_SILENCE_START,
                default=values.get(
                    CONF_NOTIFICATION_SILENCE_START,
                    DEFAULT_NOTIFICATION_SILENCE_START,
                ),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_NOTIFICATION_SILENCE_END,
                default=values.get(
                    CONF_NOTIFICATION_SILENCE_END,
                    DEFAULT_NOTIFICATION_SILENCE_END,
                ),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_NOTIFICATION_SILENCE_ENTITY,
                default=values.get(
                    CONF_NOTIFICATION_SILENCE_ENTITY,
                    DEFAULT_NOTIFICATION_SILENCE_ENTITY,
                ),
            ): selector.TextSelector(),
        }
    )


def _build_advanced_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    values = defaults or {}

    return vol.Schema(
        {
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
                CONF_CRITICAL_INDOOR_HUMIDITY,
                default=values.get(
                    CONF_CRITICAL_INDOOR_HUMIDITY,
                    DEFAULT_CRITICAL_INDOOR_HUMIDITY,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=40, max=100, step=1)
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
                CONF_MIN_INDOOR_TEMPERATURE,
                default=values.get(
                    CONF_MIN_INDOOR_TEMPERATURE,
                    DEFAULT_MIN_INDOOR_TEMPERATURE,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=25, step=0.5)
            ),
            vol.Optional(
                CONF_MAX_INDOOR_DEW_POINT_SPREAD,
                default=values.get(
                    CONF_MAX_INDOOR_DEW_POINT_SPREAD,
                    DEFAULT_MAX_INDOOR_DEW_POINT_SPREAD,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.5, max=10, step=0.1)
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
                CONF_HUMIDITY_SPIKE_THRESHOLD,
                default=values.get(
                    CONF_HUMIDITY_SPIKE_THRESHOLD,
                    DEFAULT_HUMIDITY_SPIKE_THRESHOLD,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=30, step=0.5)
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
                selector.NumberSelectorConfig(
                    min=1, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
                default=values.get(
                    CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
                    DEFAULT_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=120, step=1)
            ),
        }
    )


def _build_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """Compatibility helper for tests: full one-page schema composed from all sections."""
    values = defaults or {}
    schema: dict[vol.Marker, Any] = {}
    for section in (
        _build_basic_schema(values),
        _build_notification_schema(values),
        _build_advanced_schema(values),
    ):
        schema.update(section.schema)
    return vol.Schema(schema)


class LueftungsempfehlungConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._pending_data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending_data.update(user_input)
            return self.async_show_form(
                step_id="notifications",
                data_schema=_build_notification_schema(self._pending_data),
            )

        return self.async_show_form(step_id="user", data_schema=_build_basic_schema())

    async def async_step_notifications(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending_data.update(user_input)
            return self.async_show_form(
                step_id="advanced",
                data_schema=_build_advanced_schema(self._pending_data),
            )

        return self.async_show_form(
            step_id="notifications",
            data_schema=_build_notification_schema(self._pending_data),
        )

    async def async_step_advanced(self, user_input: dict[str, Any] | None = None):
        if user_input is None:
            return self.async_show_form(
                step_id="advanced",
                data_schema=_build_advanced_schema(self._pending_data),
            )

        self._pending_data.update(user_input)
        await self.async_set_unique_id(_build_unique_id(self._pending_data))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=self._pending_data.get(CONF_NAME, DEFAULT_NAME),
            data=self._pending_data,
        )

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
        self._config_entry = config_entry
        self._defaults: dict[str, Any] = {
            **self._config_entry.data,
            **self._config_entry.options,
        }
        self._pending_options: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending_options.update(user_input)
            defaults = {**self._defaults, **self._pending_options}
            return self.async_show_form(
                step_id="notifications",
                data_schema=_build_notification_schema(defaults),
            )

        return self.async_show_form(
            step_id="init", data_schema=_build_basic_schema(self._defaults)
        )

    async def async_step_notifications(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending_options.update(user_input)
            defaults = {**self._defaults, **self._pending_options}
            return self.async_show_form(
                step_id="advanced",
                data_schema=_build_advanced_schema(defaults),
            )

        defaults = {**self._defaults, **self._pending_options}
        return self.async_show_form(
            step_id="notifications",
            data_schema=_build_notification_schema(defaults),
        )

    async def async_step_advanced(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._pending_options.update(user_input)
            return self.async_create_entry(title="", data=self._pending_options)

        defaults = {**self._defaults, **self._pending_options}
        return self.async_show_form(
            step_id="advanced",
            data_schema=_build_advanced_schema(defaults),
        )
