from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from custom_components.lueftungsempfehlung.config_flow import (
    LueftungsempfehlungOptionsFlow,
    _build_schema,
)
from custom_components.lueftungsempfehlung.const import (
    CONF_CRITICAL_INDOOR_HUMIDITY,
    CONF_HUMIDITY_SPIKE_THRESHOLD,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MAX_INDOOR_DEW_POINT_SPREAD,
    CONF_MAX_INDOOR_HUMIDITY,
    CONF_MAX_INDOOR_TEMPERATURE,
    CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_WINDOW_ENTITY,
    REASON_HUMIDITY,
    REASON_STRUCTURE_PROTECTION_ACTIVE,
    REASON_TEMPERATURE,
    REASON_UNKNOWN,
    STATE_FENSTER_WIEDER_SCHLIESSEN,
    STATE_LUEFTEN_EMPFOHLEN,
    STATE_LUEFTEN_NICHT_EMPFOHLEN,
)
from custom_components.lueftungsempfehlung.coordinator import (
    VentilationRecommendationCoordinator,
    VentilationRecommendationData,
)
from custom_components.lueftungsempfehlung.sensor import VentilationRecommendationSensor


def _base_data(recommendation: str, reason: str) -> VentilationRecommendationData:
    return VentilationRecommendationData(
        recommendation=recommendation,
        indoor_temperature=23.0,
        indoor_humidity=55.0,
        outdoor_temperature=20.0,
        outdoor_humidity=40.0,
        indoor_absolute_humidity=10.0,
        outdoor_absolute_humidity=8.0,
        absolute_humidity_delta=2.0,
        indoor_dew_point=12.0,
        outdoor_dew_point=7.0,
        reason=reason,
        reason_detail=None,
        humidity_recommended=False,
        temperature_recommended=False,
        structure_protection_active=False,
        window_open=False,
    )


def _sensor_with_data(data: VentilationRecommendationData) -> VentilationRecommendationSensor:
    sensor = object.__new__(VentilationRecommendationSensor)
    sensor.coordinator = SimpleNamespace(data=data)
    return sensor


def _coordinator_for_notifications(data: VentilationRecommendationData) -> VentilationRecommendationCoordinator:
    coordinator = object.__new__(VentilationRecommendationCoordinator)
    coordinator.entry = SimpleNamespace(data={}, options={}, title="Test")
    coordinator.data = data
    coordinator._last_notified_recommendation = None
    coordinator._last_notification_at = None
    coordinator._reminder_count = 0

    calls: list[dict[str, str]] = []

    class _Services:
        @staticmethod
        def has_service(domain: str, service: str) -> bool:
            return domain == "notify" and service == "mobile_app_test_device"

        async def async_call(self, domain: str, service: str, payload: dict[str, str], blocking: bool = False) -> None:
            calls.append({"domain": domain, "service": service, **payload})

    coordinator.hass = SimpleNamespace(services=_Services())
    coordinator._get_notify_device_ids = lambda: ["device-1"]
    coordinator._resolve_notify_services = lambda _: ["mobile_app_test_device"]
    coordinator._calls = calls
    return coordinator


def test_sensor_icon_for_humidity_reason() -> None:
    sensor = _sensor_with_data(_base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_HUMIDITY))
    assert sensor.icon == "mdi:water-percent-alert"


def test_sensor_icon_for_temperature_reason() -> None:
    sensor = _sensor_with_data(_base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_TEMPERATURE))
    assert sensor.icon == "mdi:thermometer-alert"


def test_sensor_icon_for_structure_protection_reason() -> None:
    sensor_data = _base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_STRUCTURE_PROTECTION_ACTIVE)
    sensor_data = replace(sensor_data, structure_protection_active=True)
    sensor = _sensor_with_data(sensor_data)
    assert sensor.icon == "mdi:water-percent-alert"


def test_sensor_icon_for_default_recommendation_state() -> None:
    sensor = _sensor_with_data(_base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_UNKNOWN))
    assert sensor.icon == "mdi:window-open-variant"


@pytest.mark.asyncio
async def test_notification_sent_when_recommendation_changes_to_ventilate() -> None:
    coordinator = _coordinator_for_notifications(
        _base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_HUMIDITY)
    )

    await coordinator.async_send_notification_if_needed()

    assert len(coordinator._calls) == 1
    assert coordinator._calls[0]["title"] == "Lüften empfohlen: Test"


@pytest.mark.asyncio
async def test_notification_sent_when_recommendation_changes_to_close_window() -> None:
    coordinator = _coordinator_for_notifications(
        _base_data(STATE_FENSTER_WIEDER_SCHLIESSEN, REASON_TEMPERATURE)
    )

    await coordinator.async_send_notification_if_needed()

    assert len(coordinator._calls) == 1
    assert coordinator._calls[0]["title"] == "Fenster wieder schließen: Test"


@pytest.mark.asyncio
async def test_no_notification_for_not_recommended_transition() -> None:
    coordinator = _coordinator_for_notifications(
        _base_data(STATE_LUEFTEN_NICHT_EMPFOHLEN, REASON_TEMPERATURE)
    )

    await coordinator.async_send_notification_if_needed()

    assert coordinator._calls == []


def test_schema_applies_new_structure_protection_defaults() -> None:
    defaults = {
        CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.indoor_temp",
        CONF_INDOOR_HUMIDITY_ENTITY: "sensor.indoor_humidity",
        CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.outdoor_temp",
        CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.outdoor_humidity",
        CONF_WINDOW_ENTITY: "binary_sensor.window",
        CONF_CRITICAL_INDOOR_HUMIDITY: 77.0,
        CONF_MAX_INDOOR_DEW_POINT_SPREAD: 3.2,
        CONF_HUMIDITY_SPIKE_THRESHOLD: 6.5,
        CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES: 15,
    }

    validated = _build_schema(defaults)({})

    assert validated[CONF_CRITICAL_INDOOR_HUMIDITY] == 77.0
    assert validated[CONF_MAX_INDOOR_DEW_POINT_SPREAD] == 3.2
    assert validated[CONF_HUMIDITY_SPIKE_THRESHOLD] == 6.5
    assert validated[CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES] == 15


@pytest.mark.asyncio
async def test_options_flow_prefers_options_over_entry_data() -> None:
    flow = LueftungsempfehlungOptionsFlow(
        SimpleNamespace(
            data={
                CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.old_indoor_temp",
                CONF_INDOOR_HUMIDITY_ENTITY: "sensor.old_indoor_humidity",
                CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.old_outdoor_temp",
                CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.old_outdoor_humidity",
                    CONF_WINDOW_ENTITY: "binary_sensor.old_window",
                CONF_MAX_INDOOR_HUMIDITY: 60.0,
                CONF_MAX_INDOOR_TEMPERATURE: 24.0,
            },
            options={CONF_MAX_INDOOR_HUMIDITY: 65.0},
        )
    )

    result = await flow.async_step_init(None)
    validated = result["data_schema"]({})

    assert validated[CONF_MAX_INDOOR_HUMIDITY] == 65.0
