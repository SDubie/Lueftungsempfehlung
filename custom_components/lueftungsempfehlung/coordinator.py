from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CONF_HUMIDITY_HYSTERESIS,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MAX_INDOOR_HUMIDITY,
    CONF_MAX_INDOOR_TEMPERATURE,
    CONF_MIN_INDOOR_TEMPERATURE,
    CONF_MIN_ABSOLUTE_HUMIDITY_DELTA,
    CONF_MIN_INDOOR_HUMIDITY,
    CONF_MIN_TEMPERATURE_DELTA,
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
    DEFAULT_MAX_INDOOR_HUMIDITY,
    DEFAULT_MAX_INDOOR_TEMPERATURE,
    DEFAULT_MIN_INDOOR_TEMPERATURE,
    DOMAIN,
    DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA,
    DEFAULT_MIN_INDOOR_HUMIDITY,
    DEFAULT_MIN_TEMPERATURE_DELTA,
    DEFAULT_REMINDER_INTERVAL_MINUTES,
    DEFAULT_REMINDER_MAX_COUNT,
    DEFAULT_REQUIRE_OUTSIDE_COOLER,
    DEFAULT_TEMPERATURE_HYSTERESIS,
    REASON_DRYNESS,
    REASON_HUMIDITY,
    REASON_INDOOR_TOO_COLD,
    REASON_OUTDOOR_WARMER_AND_MORE_HUMID,
    REASON_TEMPERATURE,
    REASON_TEMPERATURE_AND_DRYNESS,
    REASON_TEMPERATURE_AND_HUMIDITY,
    REASON_UNKNOWN,
    STATE_FENSTER_WIEDER_SCHLIESSEN,
    STATE_LUEFTEN_EMPFOHLEN,
    STATE_LUEFTEN_NICHT_EMPFOHLEN,
    STATE_LUEFTEN_NICHT_NOETIG,
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
        self._last_notified_recommendation: str | None = None
        self._last_notification_at = None
        self._reminder_count = 0

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

    def initialize_notification_tracking(self) -> None:
        if self.data is not None:
            self._last_notified_recommendation = self.data.recommendation
            if self.data.recommendation == STATE_LUEFTEN_EMPFOHLEN:
                self._last_notification_at = dt_util.utcnow()
                self._reminder_count = 0

    async def async_send_notification_if_needed(self) -> None:
        if self.data is None:
            return

        now = dt_util.utcnow()
        current_recommendation = self.data.recommendation
        device_ids = self._get_notify_device_ids()

        if not device_ids:
            self._last_notified_recommendation = current_recommendation
            if current_recommendation != STATE_LUEFTEN_EMPFOHLEN:
                self._clear_reminder_tracking()
            return

        if self._last_notified_recommendation != current_recommendation:
            self._last_notified_recommendation = current_recommendation

            if current_recommendation == STATE_LUEFTEN_EMPFOHLEN:
                self._reminder_count = 0
                await self._async_dispatch_notifications(
                    title=self._build_notification_title(current_recommendation),
                    message=self._build_notification_message(),
                    device_ids=device_ids,
                )
                self._last_notification_at = now
                return

            self._clear_reminder_tracking()

            if current_recommendation == STATE_FENSTER_WIEDER_SCHLIESSEN:
                await self._async_dispatch_notifications(
                    title=self._build_notification_title(current_recommendation),
                    message=self._build_notification_message(),
                    device_ids=device_ids,
                )
            return

        if current_recommendation != STATE_LUEFTEN_EMPFOHLEN:
            return

        if not self._should_send_reminder(now):
            return

        await self._async_dispatch_notifications(
            title=self._build_notification_title(current_recommendation, is_reminder=True),
            message=self._build_notification_message(is_reminder=True),
            device_ids=device_ids,
        )
        self._last_notification_at = now
        self._reminder_count += 1

    async def _async_dispatch_notifications(
        self,
        *,
        title: str,
        message: str,
        device_ids: list[str],
    ) -> None:
        for service_name in self._resolve_notify_services(device_ids):
            if not self.hass.services.has_service("notify", service_name):
                _LOGGER.warning(
                    "Notify service notify.%s for integration %s not found",
                    service_name,
                    self.entry.title,
                )
                continue

            await self.hass.services.async_call(
                "notify",
                service_name,
                {"title": title, "message": message},
                blocking=False,
            )

    def _should_send_reminder(self, now) -> bool:
        reminder_interval = int(
            self._get_config_value(
                CONF_REMINDER_INTERVAL_MINUTES,
                DEFAULT_REMINDER_INTERVAL_MINUTES,
            )
        )
        reminder_max_count = int(
            self._get_config_value(
                CONF_REMINDER_MAX_COUNT,
                DEFAULT_REMINDER_MAX_COUNT,
            )
        )

        if reminder_max_count <= 0 or reminder_interval <= 0:
            return False

        if self._reminder_count >= reminder_max_count:
            return False

        if self._last_notification_at is None:
            return False

        return now - self._last_notification_at >= timedelta(minutes=reminder_interval)

    def _clear_reminder_tracking(self) -> None:
        self._last_notification_at = None
        self._reminder_count = 0

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
        min_indoor_temperature = float(
            self._get_config_value(
                CONF_MIN_INDOOR_TEMPERATURE,
                DEFAULT_MIN_INDOOR_TEMPERATURE,
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

        previous_active = self.data is not None and self.data.recommendation == STATE_LUEFTEN_EMPFOHLEN

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
        outside_warmer = outdoor_temperature > indoor_temperature
        outside_more_humid = outdoor_humidity > indoor_humidity
        outdoor_warmer_and_more_humid = outside_warmer and outside_more_humid
        indoor_too_cold_for_more_cooling = (
            indoor_temperature <= min_indoor_temperature and outside_cooler
        )
        ventilation_not_recommended = (
            outdoor_warmer_and_more_humid or indoor_too_cold_for_more_cooling
        )
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

        if ventilation_not_recommended:
            recommendation = (
                STATE_FENSTER_WIEDER_SCHLIESSEN
                if window_open
                else STATE_LUEFTEN_NICHT_EMPFOHLEN
            )
            reason = (
                REASON_OUTDOOR_WARMER_AND_MORE_HUMID
                if outdoor_warmer_and_more_humid
                else REASON_INDOOR_TOO_COLD
            )
        elif should_ventilate:
            recommendation = STATE_LUEFTEN_EMPFOHLEN
        else:
            recommendation = (
                STATE_FENSTER_WIEDER_SCHLIESSEN
                if window_open
                else STATE_LUEFTEN_NICHT_NOETIG
            )

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

    def _get_notify_device_ids(self) -> list[str]:
        raw_value = self._get_config_value(CONF_NOTIFY_DEVICES, [])

        if isinstance(raw_value, str):
            return [raw_value] if raw_value else []

        if isinstance(raw_value, list):
            return [device_id for device_id in raw_value if isinstance(device_id, str)]

        return []

    def _resolve_notify_services(self, device_ids: list[str]) -> list[str]:
        device_registry = dr.async_get(self.hass)
        services: list[str] = []

        for device_id in device_ids:
            device = device_registry.async_get(device_id)
            if device is None:
                _LOGGER.warning(
                    "Configured notify device %s for integration %s was not found",
                    device_id,
                    self.entry.title,
                )
                continue

            device_name = device.name_by_user or device.name
            if not device_name:
                _LOGGER.warning(
                    "Configured notify device %s for integration %s has no usable name",
                    device_id,
                    self.entry.title,
                )
                continue

            services.append(f"mobile_app_{slugify(device_name)}")

        return services

    def _build_notification_title(self, recommendation: str, is_reminder: bool = False) -> str:
        name = self.entry.title or "Lüftungsempfehlung"

        if is_reminder:
            return f"Erinnerung: Lüften empfohlen: {name}"

        if recommendation == STATE_LUEFTEN_EMPFOHLEN:
            return f"Lüften empfohlen: {name}"
        if recommendation == STATE_FENSTER_WIEDER_SCHLIESSEN:
            return f"Fenster wieder schließen: {name}"
        if recommendation == STATE_LUEFTEN_NICHT_EMPFOHLEN:
            return f"Lüften nicht empfohlen: {name}"

        return f"Lüftungsempfehlung: {name}"

    def _build_notification_message(self, is_reminder: bool = False) -> str:
        if self.data is None:
            return self.entry.title or "Lüftungsempfehlung"

        state_text = {
            STATE_LUEFTEN_EMPFOHLEN: (
                "Bitte jetzt lüften. Fenster ist weiterhin geschlossen."
                if is_reminder
                else "Bitte jetzt lüften."
            ),
            STATE_FENSTER_WIEDER_SCHLIESSEN: "Bitte Fenster wieder schließen.",
            STATE_LUEFTEN_NICHT_EMPFOHLEN: "Lüften ist aktuell nicht empfohlen.",
            STATE_LUEFTEN_NICHT_NOETIG: "Lüften ist nicht nötig.",
        }[self.data.recommendation]

        return (
            f"{state_text} "
            f"Grund: {self._build_reason_text()}. "
            f"Innen {self.data.indoor_temperature:.1f} °C / {self.data.indoor_humidity:.0f} %, "
            f"außen {self.data.outdoor_temperature:.1f} °C / {self.data.outdoor_humidity:.0f} %."
        )

    def _build_reason_text(self) -> str:
        if self.data is None:
            return REASON_UNKNOWN

        return {
            REASON_TEMPERATURE: "zu warm innen und außen ausreichend kühler",
            REASON_HUMIDITY: "innen zu feucht und außen trockener",
            REASON_DRYNESS: "innen zu trocken und außen feuchter",
            REASON_INDOOR_TOO_COLD: "innen bereits zu kalt für weiteres Lüften",
            REASON_OUTDOOR_WARMER_AND_MORE_HUMID: "außen wärmer und feuchter als innen",
            REASON_TEMPERATURE_AND_HUMIDITY: "innen zu warm und zu feucht",
            REASON_TEMPERATURE_AND_DRYNESS: "innen zu warm und zu trocken",
            REASON_UNKNOWN: "keine eindeutige Ursache",
        }[self.data.reason]

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