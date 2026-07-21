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
    ATTR_INDOOR_ABSOLUTE_HUMIDITY,
    ATTR_INDOOR_DEW_POINT,
    ATTR_OUTDOOR_ABSOLUTE_HUMIDITY,
    ATTR_OUTDOOR_DEW_POINT,
    ATTR_REASON,
    DEFAULT_NAME,
    DOMAIN,
    STATE_RECOMMENDED,
)
from .coordinator import VentilationRecommendationCoordinator

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
        return self.coordinator.data.recommendation

    @property
    def icon(self) -> str:
        if self.coordinator.data.recommendation == STATE_RECOMMENDED:
            return "mdi:window-open-variant"

        return "mdi:window-closed-variant"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            ATTR_REASON: data.reason,
            "indoor_temperature": data.indoor_temperature,
            "indoor_humidity": data.indoor_humidity,
            "outdoor_temperature": data.outdoor_temperature,
            "outdoor_humidity": data.outdoor_humidity,
            ATTR_INDOOR_ABSOLUTE_HUMIDITY: data.indoor_absolute_humidity,
            ATTR_OUTDOOR_ABSOLUTE_HUMIDITY: data.outdoor_absolute_humidity,
            ATTR_ABSOLUTE_HUMIDITY_DELTA: data.absolute_humidity_delta,
            ATTR_INDOOR_DEW_POINT: data.indoor_dew_point,
            ATTR_OUTDOOR_DEW_POINT: data.outdoor_dew_point,
        }