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
    ATTR_INDOOR_ABSOLUTE_HUMIDITY,
    ATTR_INDOOR_DEW_POINT,
    ATTR_OUTDOOR_ABSOLUTE_HUMIDITY,
    ATTR_OUTDOOR_DEW_POINT,
    ATTR_REASON,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_REQUIRE_OUTSIDE_COOLER,
    CONF_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    STATE_NOT_RECOMMENDED,
    STATE_RECOMMENDED,
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
        indoor_dew_point = self._calculate_dew_point(indoor_temperature, indoor_humidity)
        outdoor_dew_point = self._calculate_dew_point(outdoor_temperature, outdoor_humidity)

        min_delta = self.entry.options.get(
            CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
            self.entry.data[CONF_MIN_ABSOLUTE_HUMIDITY_DELTA],
        )
        require_outside_cooler = self.entry.options.get(
            CONF_REQUIRE_OUTSIDE_COOLER,
            self.entry.data[CONF_REQUIRE_OUTSIDE_COOLER],
        )

        outside_cooler = outdoor_temperature < indoor_temperature
        humidity_improves = absolute_humidity_delta >= min_delta

        if humidity_improves and (outside_cooler or not require_outside_cooler):
            recommendation = STATE_RECOMMENDED
            reason = "outside_air_is_drier"
        elif not humidity_improves:
            recommendation = STATE_NOT_RECOMMENDED
            reason = "outside_air_not_dry_enough"
        else:
            recommendation = STATE_NOT_RECOMMENDED
            reason = "outside_air_not_cooler"

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