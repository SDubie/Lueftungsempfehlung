from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

try:
    from homeassistant.helpers.device_registry import DeviceInfo
except ImportError:
    from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ABSOLUTE_HUMIDITY_DELTA,
    ATTR_HUMIDITY_RECOMMENDED,
    ATTR_INDOOR_ABSOLUTE_HUMIDITY,
    ATTR_INDOOR_DEW_POINT,
    ATTR_OUTDOOR_ABSOLUTE_HUMIDITY,
    ATTR_OUTDOOR_DEW_POINT,
    ATTR_REASON,
    ATTR_REASON_DETAIL,
    ATTR_REASON_SHORT,
    ATTR_STRUCTURE_PROTECTION_ACTIVE,
    ATTR_TEMPERATURE_RECOMMENDED,
    ATTR_WINDOW_OPEN,
    DEFAULT_NAME,
    DOMAIN,
    REASON_DETAIL_CRITICAL_HUMIDITY,
    REASON_DETAIL_DEW_POINT_RISK,
    REASON_DETAIL_HUMIDITY_SPIKE,
    REASON_DETAIL_MIN_VENTILATION_DURATION,
    REASON_DRYNESS,
    REASON_HUMIDITY,
    REASON_INDOOR_TOO_COLD,
    REASON_NO_VENTILATION_NEEDED,
    REASON_OUTDOOR_MORE_HUMID,
    REASON_OUTDOOR_WARMER,
    REASON_OUTDOOR_WARMER_AND_MORE_HUMID,
    REASON_STRUCTURE_PROTECTION_ACTIVE,
    REASON_TEMPERATURE,
    REASON_TEMPERATURE_AND_DRYNESS,
    REASON_TEMPERATURE_AND_HUMIDITY,
    REASON_UNKNOWN,
    STATE_FENSTER_WIEDER_SCHLIESSEN,
    STATE_LUEFTEN_EMPFOHLEN,
    STATE_LUEFTEN_NICHT_EMPFOHLEN,
    STATE_LUEFTEN_NICHT_NOETIG,
)
from .coordinator import VentilationRecommendationCoordinator

STATE_LABELS: dict[str, str] = {
    STATE_LUEFTEN_NICHT_NOETIG: "Lüften nicht nötig",
    STATE_LUEFTEN_EMPFOHLEN: "Lüften empfohlen",
    STATE_LUEFTEN_NICHT_EMPFOHLEN: "Lüften nicht empfohlen",
    STATE_FENSTER_WIEDER_SCHLIESSEN: "Fenster wieder schließen",
}

REASON_LABELS: dict[str, str] = {
    REASON_TEMPERATURE: "Zu warm innen, außen ausreichend kühler",
    REASON_HUMIDITY: "Innen zu feucht, außen trockener",
    REASON_DRYNESS: "Innen zu trocken, außen feuchter",
    REASON_INDOOR_TOO_COLD: "Innen bereits zu kalt für weiteres Lüften",
    REASON_OUTDOOR_WARMER: "Außen wärmer als innen",
    REASON_OUTDOOR_WARMER_AND_MORE_HUMID: "Außen wärmer und feuchter als innen",
    REASON_OUTDOOR_MORE_HUMID: "Außen feuchter als innen",
    REASON_STRUCTURE_PROTECTION_ACTIVE: "Strukturschutz aktiv",
    REASON_TEMPERATURE_AND_HUMIDITY: "Zu warm und zu feucht",
    REASON_TEMPERATURE_AND_DRYNESS: "Zu warm und zu trocken",
    REASON_NO_VENTILATION_NEEDED: "Kein Lüftungsbedarf",
    REASON_UNKNOWN: "Kein eindeutiger Lüftungsgrund",
}

REASON_SHORT_LABELS: dict[str, str] = {
    REASON_TEMPERATURE: "Zu warm",
    REASON_HUMIDITY: "Zu feucht",
    REASON_DRYNESS: "Zu trocken",
    REASON_INDOOR_TOO_COLD: "Innen zu kalt",
    REASON_OUTDOOR_WARMER: "Außen wärmer",
    REASON_OUTDOOR_WARMER_AND_MORE_HUMID: "Außen wärmer + feuchter",
    REASON_OUTDOOR_MORE_HUMID: "Außen feuchter",
    REASON_STRUCTURE_PROTECTION_ACTIVE: "Strukturschutz",
    REASON_TEMPERATURE_AND_HUMIDITY: "Zu warm + feucht",
    REASON_TEMPERATURE_AND_DRYNESS: "Zu warm + trocken",
    REASON_NO_VENTILATION_NEEDED: "Kein Lüftungsbedarf",
    REASON_UNKNOWN: "Unklar",
}

REASON_DETAIL_LABELS: dict[str, str] = {
    REASON_DETAIL_CRITICAL_HUMIDITY: "Kritische Innenfeuchtigkeit",
    REASON_DETAIL_DEW_POINT_RISK: "Hohes Taupunkt-/Kondensationsrisiko",
    REASON_DETAIL_HUMIDITY_SPIKE: "Schneller Feuchteanstieg innen",
    REASON_DETAIL_MIN_VENTILATION_DURATION: "Mindestlüftungsdauer für Entfeuchtung aktiv",
}

SENSOR_DESCRIPTION = SensorEntityDescription(
    key="ventilation_recommendation",
    translation_key="ventilation_recommendation",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VentilationRecommendationCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    async_add_entities([VentilationRecommendationSensor(coordinator, entry)])


class VentilationRecommendationSensor(
    CoordinatorEntity[VentilationRecommendationCoordinator], SensorEntity
):
    _attr_has_entity_name = True
    _attr_name = None
    entity_description = SENSOR_DESCRIPTION

    def __init__(
        self,
        coordinator: VentilationRecommendationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ventilation_recommendation"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or DEFAULT_NAME,
            manufacturer="Custom",
            model="Ventilation Recommendation",
        )

    @property
    def native_value(self) -> str | None:
        recommendation = self.coordinator.data.recommendation
        return STATE_LABELS.get(recommendation, recommendation)

    @property
    def icon(self) -> str:
        if self.coordinator.data.reason == REASON_STRUCTURE_PROTECTION_ACTIVE:
            return "mdi:water-percent-alert"

        if self.coordinator.data.reason in {
            REASON_HUMIDITY,
            REASON_DRYNESS,
            REASON_TEMPERATURE_AND_HUMIDITY,
            REASON_TEMPERATURE_AND_DRYNESS,
            REASON_STRUCTURE_PROTECTION_ACTIVE,
        }:
            return "mdi:water-percent-alert"

        if self.coordinator.data.reason in {
            REASON_TEMPERATURE,
        }:
            return "mdi:thermometer-alert"

        if self.coordinator.data.recommendation == STATE_LUEFTEN_EMPFOHLEN:
            return "mdi:window-open-variant"

        return "mdi:window-closed-variant"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            ATTR_REASON: REASON_LABELS.get(data.reason, data.reason),
            ATTR_REASON_SHORT: REASON_SHORT_LABELS.get(data.reason, data.reason),
            ATTR_REASON_DETAIL: (
                REASON_DETAIL_LABELS.get(data.reason_detail, data.reason_detail)
                if data.reason_detail
                else None
            ),
            "reason_code": data.reason,
            "reason_detail_code": data.reason_detail,
            "status_code": data.recommendation,
            "indoor_temperature": data.indoor_temperature,
            "indoor_humidity": data.indoor_humidity,
            "outdoor_temperature": data.outdoor_temperature,
            "outdoor_humidity": data.outdoor_humidity,
            ATTR_INDOOR_ABSOLUTE_HUMIDITY: data.indoor_absolute_humidity,
            ATTR_OUTDOOR_ABSOLUTE_HUMIDITY: data.outdoor_absolute_humidity,
            ATTR_ABSOLUTE_HUMIDITY_DELTA: data.absolute_humidity_delta,
            ATTR_INDOOR_DEW_POINT: data.indoor_dew_point,
            ATTR_OUTDOOR_DEW_POINT: data.outdoor_dew_point,
            ATTR_HUMIDITY_RECOMMENDED: data.humidity_recommended,
            ATTR_TEMPERATURE_RECOMMENDED: data.temperature_recommended,
            ATTR_STRUCTURE_PROTECTION_ACTIVE: data.structure_protection_active,
            ATTR_WINDOW_OPEN: data.window_open,
        }
