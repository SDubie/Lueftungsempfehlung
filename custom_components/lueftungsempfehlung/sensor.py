from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
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
    ATTR_TEMPERATURE_RECOMMENDED,
    ATTR_WINDOW_OPEN,
    DEFAULT_NAME,
    DOMAIN,
    STATE_JETZT_LUEFTEN,
    STATE_NICHT_MEHR_LUEFTEN,
    STATE_WEITER_LUEFTEN,
    STATE_ALLES_OK,
    REASON_TEMPERATURE,
    REASON_HUMIDITY,
    REASON_DRYNESS,
    REASON_TEMPERATURE_AND_HUMIDITY,
    REASON_TEMPERATURE_AND_DRYNESS,
    REASON_UNKNOWN,
)
from .coordinator import VentilationRecommendationCoordinator


STATE_LABELS: dict[str, str] = {
    STATE_JETZT_LUEFTEN: "Jetzt lüften",
    STATE_WEITER_LUEFTEN: "Weiter lüften",
    STATE_NICHT_MEHR_LUEFTEN: "Nicht mehr lüften",
    STATE_ALLES_OK: "Alles ok",
}

REASON_LABELS: dict[str, str] = {
    REASON_TEMPERATURE: "Zu warm innen, außen ausreichend kühler",
    REASON_HUMIDITY: "Innen zu feucht, außen trockener",
    REASON_DRYNESS: "Innen zu trocken, außen feuchter",
    REASON_TEMPERATURE_AND_HUMIDITY: "Zu warm und zu feucht",
    REASON_TEMPERATURE_AND_DRYNESS: "Zu warm und zu trocken",
    REASON_UNKNOWN: "Kein eindeutiger Lüftungsgrund",
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
    coordinator: VentilationRecommendationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VentilationRecommendationSensor(coordinator, entry)])


class VentilationRecommendationSensor(
    CoordinatorEntity[VentilationRecommendationCoordinator], SensorEntity
):
    _attr_has_entity_name = True
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
        if self.coordinator.data.recommendation in {
            STATE_JETZT_LUEFTEN,
            STATE_WEITER_LUEFTEN,
        }:
            return "mdi:window-open-variant"

        return "mdi:window-closed-variant"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            ATTR_REASON: REASON_LABELS.get(data.reason, data.reason),
            "reason_code": data.reason,
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
            ATTR_WINDOW_OPEN: data.window_open,
        }