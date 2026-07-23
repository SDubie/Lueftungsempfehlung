from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_ABSOLUTE_HUMIDITY_DELTA,
    ATTR_HUMIDITY_RECOMMENDED,
    ATTR_INDOOR_ABSOLUTE_HUMIDITY,
    ATTR_INDOOR_DEW_POINT,
    ATTR_OUTDOOR_ABSOLUTE_HUMIDITY,
    ATTR_OUTDOOR_DEW_POINT,
    ATTR_REASON,
    ATTR_TEMPERATURE_RECOMMENDED,
    ATTR_WINDOW_OPEN,
    CONF_HUMIDITY_HYSTERESIS,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MAX_INDOOR_HUMIDITY,
    CONF_MAX_INDOOR_TEMPERATURE,
    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
    CONF_MIN_INDOOR_HUMIDITY,
    CONF_MIN_TEMPERATURE_DELTA,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_REQUIRE_OUTSIDE_COOLER,
    CONF_TEMPERATURE_HYSTERESIS,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_WINDOW_ENTITY,
    DEFAULT_HUMIDITY_HYSTERESIS,
    DEFAULT_MAX_INDOOR_HUMIDITY,
    DEFAULT_MAX_INDOOR_TEMPERATURE,
    DOMAIN,
    DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
    DEFAULT_MIN_INDOOR_HUMIDITY,
    DEFAULT_MIN_TEMPERATURE_DELTA,
    DEFAULT_REQUIRE_OUTSIDE_COOLER,
    DEFAULT_TEMPERATURE_HYSTERESIS,
    REASON_DRYNESS,
    REASON_HUMIDITY,
    REASON_TEMPERATURE,
    REASON_TEMPERATURE_AND_DRYNESS,
    REASON_TEMPERATURE_AND_HUMIDITY,
    REASON_UNKNOWN,
    STATE_ALLES_OK,
    STATE_JETZT_LUEFTEN,
    STATE_NICHT_MEHR_LUEFTEN,
    STATE_WEITER_LUEFTEN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class VentilationRecommendationData:
    recommendation: str
    indoor_temperature: float
    indoor_humidity: float
    outdoor_temperature: float
    outdoor_humidity: float
    indoor_absolute_humidity: float
    outdoor_absolute_humidity: float
    absolute_humidity_delta: float
    indoor_dew_point: float
    outdoor_dew_point: float
    reason: str
    humidity_recommended: bool
    temperature_recommended: bool
    window_open: bool


class VentilationRecommendationCoordinator(
    DataUpdateCoordinator[VentilationRecommendationData]
):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(
                    CONF_UPDATE_INTERVAL_MINUTES,
                    entry.data[CONF_UPDATE_INTERVAL_MINUTES],
                )
            ),
        )

    def _get_config_value(self, key: str, default: bool | float | int | str) -> bool | float | int | str:
        return self.entry.options.get(key, self.entry.data.get(key, default))

    async def _async_update_data(self) -> VentilationRecommendationData:
        try:
            indoor_temperature = self._get_float_state(
                self.entry.data[CONF_INDOOR_TEMPERATURE_ENTITY]
            )
            indoor_humidity = self._get_float_state(
                self.entry.data[CONF_INDOOR_HUMIDITY_ENTITY]
            )
            outdoor_temperature = self._get_float_state(
                self.entry.data[CONF_OUTDOOR_TEMPERATURE_ENTITY]
            )
            outdoor_humidity = self._get_float_state(
                self.entry.data[CONF_OUTDOOR_HUMIDITY_ENTITY]
            )
            window_open = self._get_window_open_state(
                self.entry.data.get(CONF_WINDOW_ENTITY)
            )
        except HomeAssistantError as err:
            raise UpdateFailed(str(err)) from err

        indoor_absolute_humidity = self._calculate_absolute_humidity(
            indoor_temperature,
            indoor_humidity,
        )
        outdoor_absolute_humidity = self._calculate_absolute_humidity(
            outdoor_temperature,
            outdoor_humidity,
        )
        absolute_humidity_delta = indoor_absolute_humidity - outdoor_absolute_humidity
        reverse_absolute_humidity_delta = outdoor_absolute_humidity - indoor_absolute_humidity
        indoor_dew_point = self._calculate_dew_point(indoor_temperature, indoor_humidity)
        outdoor_dew_point = self._calculate_dew_point(outdoor_temperature, outdoor_humidity)

        min_delta = float(
            self._get_config_value(
                CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
                DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
            )
        )
        max_indoor_humidity = float(
            self._get_config_value(
                CONF_MAX_INDOOR_HUMIDITY,
                DEFAULT_MAX_INDOOR_HUMIDITY,
            )
        )
        min_indoor_humidity = float(
            self._get_config_value(
                CONF_MIN_INDOOR_HUMIDITY,
                DEFAULT_MIN_INDOOR_HUMIDITY,
            )
        )
        max_indoor_temperature = float(
            self._get_config_value(
                CONF_MAX_INDOOR_TEMPERATURE,
                DEFAULT_MAX_INDOOR_TEMPERATURE,
            )
        )
        min_temperature_delta = float(
            self._get_config_value(
                CONF_MIN_TEMPERATURE_DELTA,
                DEFAULT_MIN_TEMPERATURE_DELTA,
            )
        )
        humidity_hysteresis = float(
            self._get_config_value(
                CONF_HUMIDITY_HYSTERESIS,
                DEFAULT_HUMIDITY_HYSTERESIS,
            )
        )
        temperature_hysteresis = float(
            self._get_config_value(
                CONF_TEMPERATURE_HYSTERESIS,
                DEFAULT_TEMPERATURE_HYSTERESIS,
            )
        )
        require_outside_cooler = bool(
            self._get_config_value(
                CONF_REQUIRE_OUTSIDE_COOLER,
                DEFAULT_REQUIRE_OUTSIDE_COOLER,
            )
        )

        previous_active = self.data is not None and self.data.recommendation in {
            STATE_JETZT_LUEFTEN,
            STATE_WEITER_LUEFTEN,
        }

        humidity_delta_threshold = min_delta - humidity_hysteresis if previous_active else min_delta
        temperature_delta_threshold = (
            min_temperature_delta - temperature_hysteresis
            if previous_active
            else min_temperature_delta
        )
        humidity_delta_threshold = max(humidity_delta_threshold, 0)
        temperature_delta_threshold = max(temperature_delta_threshold, 0)

        too_humid = (
            indoor_humidity >= max_indoor_humidity
            and absolute_humidity_delta >= humidity_delta_threshold
        )
        too_dry = (
            min_indoor_humidity > 0
            and indoor_humidity <= min_indoor_humidity
            and reverse_absolute_humidity_delta >= humidity_delta_threshold
        )
        humidity_recommended = too_humid or too_dry

        temp_diff = indoor_temperature - outdoor_temperature
        outside_cooler = outdoor_temperature < indoor_temperature
        temperature_recommended = (
            indoor_temperature >= max_indoor_temperature
            and temp_diff >= temperature_delta_threshold
            and (outside_cooler or not require_outside_cooler)
        )

        if temperature_recommended and too_humid:
            reason = REASON_TEMPERATURE_AND_HUMIDITY
        elif temperature_recommended and too_dry:
            reason = REASON_TEMPERATURE_AND_DRYNESS
        elif temperature_recommended:
            reason = REASON_TEMPERATURE
        elif too_humid:
            reason = REASON_HUMIDITY
        elif too_dry:
            reason = REASON_DRYNESS
        else:
            reason = REASON_UNKNOWN

        should_ventilate = humidity_recommended or temperature_recommended

        if should_ventilate:
            recommendation = STATE_WEITER_LUEFTEN if window_open else STATE_JETZT_LUEFTEN
        else:
            recommendation = STATE_NICHT_MEHR_LUEFTEN if window_open else STATE_ALLES_OK

        return VentilationRecommendationData(
            recommendation=recommendation,
            indoor_temperature=round(indoor_temperature, 2),
            indoor_humidity=round(indoor_humidity, 2),
            outdoor_temperature=round(outdoor_temperature, 2),
            outdoor_humidity=round(outdoor_humidity, 2),
            indoor_absolute_humidity=round(indoor_absolute_humidity, 2),
            outdoor_absolute_humidity=round(outdoor_absolute_humidity, 2),
            absolute_humidity_delta=round(absolute_humidity_delta, 2),
            indoor_dew_point=round(indoor_dew_point, 2),
            outdoor_dew_point=round(outdoor_dew_point, 2),
            reason=reason,
            humidity_recommended=humidity_recommended,
            temperature_recommended=temperature_recommended,
            window_open=window_open,
        )

    def _get_float_state(self, entity_id: str) -> float:
        state = self.hass.states.get(entity_id)

        if state is None:
            raise HomeAssistantError(f"Entity not found: {entity_id}")

        if state.state in {STATE_UNKNOWN, STATE_UNAVAILABLE}:
            raise HomeAssistantError(f"Entity state unavailable: {entity_id}")

        try:
            return float(state.state)
        except ValueError as err:
            raise HomeAssistantError(
                f"Entity state is not numeric: {entity_id}={state.state}"
            ) from err

    def _get_window_open_state(self, entity_id: str | None) -> bool:
        if not entity_id:
            return False

        state = self.hass.states.get(entity_id)

        if state is None:
            raise HomeAssistantError(f"Entity not found: {entity_id}")

        if state.state in {STATE_UNKNOWN, STATE_UNAVAILABLE}:
            raise HomeAssistantError(f"Entity state unavailable: {entity_id}")

        return state.state in {"on", "open"}

    @staticmethod
    def _calculate_absolute_humidity(temperature_c: float, humidity_percent: float) -> float:
        saturation_vapor_pressure = 6.112 * math.exp(
            (17.67 * temperature_c) / (temperature_c + 243.5)
        )
        vapor_pressure = saturation_vapor_pressure * (humidity_percent / 100)
        return 216.7 * (vapor_pressure / (273.15 + temperature_c))

    @staticmethod
    def _calculate_dew_point(temperature_c: float, humidity_percent: float) -> float:
        humidity = max(min(humidity_percent, 100), 1)
        alpha = math.log(humidity / 100) + (
            (17.62 * temperature_c) / (243.12 + temperature_c)
        )
        return (243.12 * alpha) / (17.62 - alpha)