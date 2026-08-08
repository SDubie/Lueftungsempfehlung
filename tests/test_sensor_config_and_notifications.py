from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest
from homeassistant import data_entry_flow

from custom_components.lueftungsempfehlung.config_flow import (
    LueftungsempfehlungConfigFlow,
    LueftungsempfehlungOptionsFlow,
    _build_schema,
)
from custom_components.lueftungsempfehlung.const import (
    ATTR_REASON_SHORT,
    CONF_CRITICAL_INDOOR_HUMIDITY,
    CONF_HUMIDITY_SPIKE_THRESHOLD,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_MAX_INDOOR_DEW_POINT_SPREAD,
    CONF_MAX_INDOOR_HUMIDITY,
    CONF_MAX_INDOOR_TEMPERATURE,
    CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES,
    CONF_NAME,
    CONF_NOTIFICATION_SILENCE_END,
    CONF_NOTIFICATION_SILENCE_ENTITY,
    CONF_NOTIFICATION_SILENCE_START,
    CONF_NOTIFY_DEVICES,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_REMINDER_INTERVAL_MINUTES,
    CONF_REMINDER_MAX_COUNT,
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


def _sensor_with_data(
    data: VentilationRecommendationData,
) -> VentilationRecommendationSensor:
    sensor = object.__new__(VentilationRecommendationSensor)
    sensor.coordinator = SimpleNamespace(data=data)
    return sensor


def _coordinator_for_notifications(
    data: VentilationRecommendationData,
) -> VentilationRecommendationCoordinator:
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

        async def async_call(
            self,
            domain: str,
            service: str,
            payload: dict[str, str],
            blocking: bool = False,
        ) -> None:
            calls.append({"domain": domain, "service": service, **payload})

    coordinator.hass = SimpleNamespace(
        services=_Services(),
        states=SimpleNamespace(get=lambda _: None),
    )
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
    sensor_data = _base_data(
        STATE_LUEFTEN_EMPFOHLEN, REASON_STRUCTURE_PROTECTION_ACTIVE
    )
    sensor_data = replace(sensor_data, structure_protection_active=True)
    sensor = _sensor_with_data(sensor_data)
    assert sensor.icon == "mdi:water-percent-alert"


def test_sensor_icon_for_default_recommendation_state() -> None:
    sensor = _sensor_with_data(_base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_UNKNOWN))
    assert sensor.icon == "mdi:window-open-variant"


def test_sensor_exposes_short_reason_attribute() -> None:
    sensor = _sensor_with_data(_base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_HUMIDITY))

    assert sensor.extra_state_attributes[ATTR_REASON_SHORT] == "Zu feucht"


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


@pytest.mark.asyncio
async def test_no_notification_when_silence_window_is_active() -> None:
    coordinator = _coordinator_for_notifications(
        _base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_HUMIDITY)
    )
    coordinator.entry.options = {
        CONF_NOTIFICATION_SILENCE_START: "00:00",
        CONF_NOTIFICATION_SILENCE_END: "23:59",
    }

    await coordinator.async_send_notification_if_needed()

    assert coordinator._calls == []


@pytest.mark.asyncio
async def test_no_notification_when_external_silence_entity_is_active() -> None:
    coordinator = _coordinator_for_notifications(
        _base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_HUMIDITY)
    )
    coordinator.entry.options = {
        CONF_NOTIFICATION_SILENCE_ENTITY: "schedule.notification_quiet_hours"
    }
    coordinator.hass = SimpleNamespace(
        services=coordinator.hass.services,
        states=SimpleNamespace(get=lambda _: SimpleNamespace(state="on")),
    )

    await coordinator.async_send_notification_if_needed()

    assert coordinator._calls == []


def test_notification_message_uses_absolute_humidity_for_humidity_reason() -> None:
    coordinator = _coordinator_for_notifications(
        _base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_HUMIDITY)
    )

    message = coordinator._build_notification_message()

    assert "Grund: Zu feucht." in message
    assert "10.0 g/m³" in message
    assert "8.0 g/m³" in message
    assert "55 %" not in message
    assert "40 %" not in message


def test_notification_message_uses_relative_humidity_for_non_humidity_reason() -> None:
    coordinator = _coordinator_for_notifications(
        _base_data(STATE_LUEFTEN_EMPFOHLEN, REASON_TEMPERATURE)
    )

    message = coordinator._build_notification_message()

    assert "55 %" in message
    assert "40 %" in message


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
        CONF_NOTIFICATION_SILENCE_START: "22:00",
        CONF_NOTIFICATION_SILENCE_END: "07:00",
        CONF_NOTIFICATION_SILENCE_ENTITY: "schedule.notification_quiet_hours",
    }

    validated = _build_schema(defaults)({})

    assert validated[CONF_CRITICAL_INDOOR_HUMIDITY] == 77.0
    assert validated[CONF_MAX_INDOOR_DEW_POINT_SPREAD] == 3.2
    assert validated[CONF_HUMIDITY_SPIKE_THRESHOLD] == 6.5
    assert validated[CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES] == 15
    assert validated[CONF_NOTIFICATION_SILENCE_START] == "22:00"
    assert validated[CONF_NOTIFICATION_SILENCE_END] == "07:00"
    assert (
        validated[CONF_NOTIFICATION_SILENCE_ENTITY]
        == "schedule.notification_quiet_hours"
    )


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
    assert result["step_id"] == "init"

    notifications_step = await flow.async_step_init(
        {
            CONF_NAME: "Test",
            CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.indoor_temp",
            CONF_INDOOR_HUMIDITY_ENTITY: "sensor.indoor_humidity",
            CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.outdoor_temp",
            CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.outdoor_humidity",
            CONF_WINDOW_ENTITY: "binary_sensor.window",
        }
    )
    assert notifications_step["step_id"] == "notifications"

    advanced_step = await flow.async_step_notifications(
        {
            CONF_NOTIFY_DEVICES: [],
            CONF_REMINDER_INTERVAL_MINUTES: 60,
            CONF_REMINDER_MAX_COUNT: 3,
            CONF_NOTIFICATION_SILENCE_START: "",
            CONF_NOTIFICATION_SILENCE_END: "",
            CONF_NOTIFICATION_SILENCE_ENTITY: "",
        }
    )
    assert advanced_step["step_id"] == "advanced"
    validated = advanced_step["data_schema"]({})

    assert validated[CONF_MAX_INDOOR_HUMIDITY] == 65.0


@pytest.mark.asyncio
async def test_config_flow_runs_through_three_steps() -> None:
    flow = LueftungsempfehlungConfigFlow()

    step_user = await flow.async_step_user(None)
    assert step_user["type"] == data_entry_flow.FlowResultType.FORM
    assert step_user["step_id"] == "user"

    step_notifications = await flow.async_step_user(
        {
            CONF_NAME: "Test",
            CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.indoor_temp",
            CONF_INDOOR_HUMIDITY_ENTITY: "sensor.indoor_humidity",
            CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.outdoor_temp",
            CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.outdoor_humidity",
            CONF_WINDOW_ENTITY: "",
        }
    )
    assert step_notifications["type"] == data_entry_flow.FlowResultType.FORM
    assert step_notifications["step_id"] == "notifications"

    step_advanced = await flow.async_step_notifications(
        {
            CONF_NOTIFY_DEVICES: [],
            CONF_REMINDER_INTERVAL_MINUTES: 60,
            CONF_REMINDER_MAX_COUNT: 3,
            CONF_NOTIFICATION_SILENCE_START: "",
            CONF_NOTIFICATION_SILENCE_END: "",
            CONF_NOTIFICATION_SILENCE_ENTITY: "",
        }
    )
    assert step_advanced["type"] == data_entry_flow.FlowResultType.FORM
    assert step_advanced["step_id"] == "advanced"


@pytest.mark.asyncio
async def test_config_flow_duplicate_combination_shows_existing_sensor_name() -> None:
    flow = LueftungsempfehlungConfigFlow()
    flow._pending_data = {
        CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.indoor_temp",
        CONF_INDOOR_HUMIDITY_ENTITY: "sensor.indoor_humidity",
        CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.outdoor_temp",
        CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.outdoor_humidity",
    }
    flow._async_current_entries = lambda: [
        SimpleNamespace(
            unique_id=(
                "sensor.indoor_temp|sensor.indoor_humidity|"
                "sensor.outdoor_temp|sensor.outdoor_humidity"
            ),
            title="Lüftungsempfehlung Bad",
            entry_id="entry-1",
        )
    ]

    result = await flow.async_step_advanced({})

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert result["description_placeholders"] == {"name": "Lüftungsempfehlung Bad"}


@pytest.mark.asyncio
async def test_options_flow_runs_through_three_steps() -> None:
    flow = LueftungsempfehlungOptionsFlow(
        SimpleNamespace(
            data={
                CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.old_indoor_temp",
                CONF_INDOOR_HUMIDITY_ENTITY: "sensor.old_indoor_humidity",
                CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.old_outdoor_temp",
                CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.old_outdoor_humidity",
            },
            options={},
        )
    )

    step_init = await flow.async_step_init(None)
    assert step_init["type"] == data_entry_flow.FlowResultType.FORM
    assert step_init["step_id"] == "init"

    step_notifications = await flow.async_step_init(
        {
            CONF_NAME: "Test",
            CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.indoor_temp",
            CONF_INDOOR_HUMIDITY_ENTITY: "sensor.indoor_humidity",
            CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.outdoor_temp",
            CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.outdoor_humidity",
            CONF_WINDOW_ENTITY: "",
        }
    )
    assert step_notifications["type"] == data_entry_flow.FlowResultType.FORM
    assert step_notifications["step_id"] == "notifications"

    step_advanced = await flow.async_step_notifications(
        {
            CONF_NOTIFY_DEVICES: [],
            CONF_REMINDER_INTERVAL_MINUTES: 60,
            CONF_REMINDER_MAX_COUNT: 3,
            CONF_NOTIFICATION_SILENCE_START: "",
            CONF_NOTIFICATION_SILENCE_END: "",
            CONF_NOTIFICATION_SILENCE_ENTITY: "",
        }
    )
    assert step_advanced["type"] == data_entry_flow.FlowResultType.FORM
    assert step_advanced["step_id"] == "advanced"
