from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from types import SimpleNamespace

import pytest

from homeassistant.util import dt as dt_util

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
    REASON_DETAIL_CRITICAL_HUMIDITY,
    REASON_DETAIL_DEW_POINT_RISK,
    REASON_DETAIL_HUMIDITY_SPIKE,
    REASON_DETAIL_MIN_VENTILATION_DURATION,
    REASON_NO_VENTILATION_NEEDED,
    REASON_OUTDOOR_MORE_HUMID,
    REASON_OUTDOOR_WARMER,
    REASON_OUTDOOR_WARMER_AND_MORE_HUMID,
    REASON_STRUCTURE_PROTECTION_ACTIVE,
    STATE_FENSTER_WIEDER_SCHLIESSEN,
    STATE_LUEFTEN_EMPFOHLEN,
    STATE_LUEFTEN_NICHT_EMPFOHLEN,
    STATE_LUEFTEN_NICHT_NOETIG,
)
from custom_components.lueftungsempfehlung.coordinator import (
    VentilationRecommendationCoordinator,
    VentilationRecommendationData,
)


@dataclass
class _FakeState:
    state: str


class _FakeStates:
    def __init__(self, values: dict[str, float | int | str]) -> None:
        self._values = {entity_id: _FakeState(str(value)) for entity_id, value in values.items()}

    def get(self, entity_id: str):
        return self._values.get(entity_id)


class _FakeHass:
    def __init__(self, values: dict[str, float | int | str]) -> None:
        self.states = _FakeStates(values)


def _base_entry_data() -> dict[str, str | float | int | bool | list[str]]:
    return {
        CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.indoor_temp",
        CONF_INDOOR_HUMIDITY_ENTITY: "sensor.indoor_humidity",
        CONF_OUTDOOR_TEMPERATURE_ENTITY: "sensor.outdoor_temp",
        CONF_OUTDOOR_HUMIDITY_ENTITY: "sensor.outdoor_humidity",
        CONF_WINDOW_ENTITY: "",
    }


def _build_coordinator(
    *,
    states: dict[str, float | int | str],
    options: dict[str, float | int | bool] | None = None,
    previous_data: VentilationRecommendationData | None = None,
) -> VentilationRecommendationCoordinator:
    coordinator = object.__new__(VentilationRecommendationCoordinator)
    coordinator.entry = SimpleNamespace(
        data=_base_entry_data(),
        options=options or {},
        title="Test",
    )
    coordinator.hass = _FakeHass(states)
    coordinator.data = previous_data
    coordinator._structure_protection_started_at = None
    coordinator._last_notified_recommendation = None
    coordinator._last_notification_at = None
    coordinator._reminder_count = 0
    return coordinator


def _default_options() -> dict[str, float | int | bool]:
    return {
        CONF_MAX_INDOOR_HUMIDITY: 60.0,
        CONF_MAX_INDOOR_TEMPERATURE: 30.0,
        CONF_CRITICAL_INDOOR_HUMIDITY: 85.0,
        CONF_MAX_INDOOR_DEW_POINT_SPREAD: 1.0,
        CONF_HUMIDITY_SPIKE_THRESHOLD: 99.0,
        CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES: 0,
    }


@pytest.mark.asyncio
async def test_not_recommended_when_outdoor_more_humid() -> None:
    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 24.0,
            "sensor.indoor_humidity": 65.0,
            "sensor.outdoor_temp": 22.0,
            "sensor.outdoor_humidity": 80.0,
        },
        options=_default_options(),
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_NICHT_EMPFOHLEN
    assert result.reason == REASON_OUTDOOR_MORE_HUMID


@pytest.mark.asyncio
async def test_not_needed_sets_explicit_no_ventilation_reason() -> None:
    options = _default_options()
    options[CONF_MAX_INDOOR_HUMIDITY] = 70.0
    options[CONF_MAX_INDOOR_TEMPERATURE] = 30.0

    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 22.0,
            "sensor.indoor_humidity": 50.0,
            "sensor.outdoor_temp": 20.0,
            "sensor.outdoor_humidity": 45.0,
        },
        options=options,
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_NICHT_NOETIG
    assert result.reason == REASON_NO_VENTILATION_NEEDED


@pytest.mark.asyncio
async def test_close_window_sets_explicit_no_ventilation_reason() -> None:
    options = _default_options()
    options[CONF_MAX_INDOOR_HUMIDITY] = 70.0
    options[CONF_MAX_INDOOR_TEMPERATURE] = 30.0

    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 22.0,
            "sensor.indoor_humidity": 50.0,
            "sensor.outdoor_temp": 20.0,
            "sensor.outdoor_humidity": 45.0,
            "binary_sensor.window": "on",
        },
        options=options,
    )
    coordinator.entry.data[CONF_WINDOW_ENTITY] = "binary_sensor.window"

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_FENSTER_WIEDER_SCHLIESSEN
    assert result.reason == REASON_NO_VENTILATION_NEEDED


@pytest.mark.asyncio
async def test_recommended_when_outdoor_relative_humidity_is_higher_but_absolute_humidity_is_lower() -> None:
    options = _default_options()
    options[CONF_MAX_INDOOR_HUMIDITY] = 55.0

    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 24.0,
            "sensor.indoor_humidity": 60.0,
            "sensor.outdoor_temp": 8.0,
            "sensor.outdoor_humidity": 90.0,
        },
        options=options,
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_EMPFOHLEN


@pytest.mark.asyncio
async def test_recommended_when_outdoor_warmer_but_humidity_reduction_possible() -> None:
    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 24.0,
            "sensor.indoor_humidity": 65.0,
            "sensor.outdoor_temp": 28.0,
            "sensor.outdoor_humidity": 35.0,
        },
        options=_default_options(),
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_EMPFOHLEN


@pytest.mark.asyncio
async def test_not_recommended_when_outdoor_warmer_and_absolute_more_humid() -> None:
    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 22.0,
            "sensor.indoor_humidity": 50.0,
            "sensor.outdoor_temp": 28.0,
            "sensor.outdoor_humidity": 50.0,
        },
        options=_default_options(),
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_NICHT_EMPFOHLEN
    assert result.reason == REASON_OUTDOOR_WARMER_AND_MORE_HUMID


@pytest.mark.asyncio
async def test_structure_protection_triggers_for_critical_humidity() -> None:
    options = _default_options()
    options[CONF_CRITICAL_INDOOR_HUMIDITY] = 70.0

    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 24.0,
            "sensor.indoor_humidity": 72.0,
            "sensor.outdoor_temp": 30.0,
            "sensor.outdoor_humidity": 40.0,
        },
        options=options,
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_EMPFOHLEN
    assert result.reason == REASON_STRUCTURE_PROTECTION_ACTIVE
    assert result.reason_detail == REASON_DETAIL_CRITICAL_HUMIDITY
    assert result.structure_protection_active is True


@pytest.mark.asyncio
async def test_structure_protection_triggers_for_dew_point_risk() -> None:
    options = _default_options()
    options[CONF_MAX_INDOOR_DEW_POINT_SPREAD] = 2.5
    options[CONF_MAX_INDOOR_HUMIDITY] = 90.0
    options[CONF_CRITICAL_INDOOR_HUMIDITY] = 95.0

    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 20.0,
            "sensor.indoor_humidity": 88.0,
            "sensor.outdoor_temp": 18.0,
            "sensor.outdoor_humidity": 55.0,
        },
        options=options,
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_EMPFOHLEN
    assert result.reason == REASON_STRUCTURE_PROTECTION_ACTIVE
    assert result.reason_detail == REASON_DETAIL_DEW_POINT_RISK


@pytest.mark.asyncio
async def test_structure_protection_triggers_for_humidity_spike() -> None:
    options = _default_options()
    options[CONF_MAX_INDOOR_HUMIDITY] = 90.0
    options[CONF_HUMIDITY_SPIKE_THRESHOLD] = 4.0

    previous = VentilationRecommendationData(
        recommendation=STATE_LUEFTEN_EMPFOHLEN,
        indoor_temperature=22.0,
        indoor_humidity=50.0,
        outdoor_temperature=20.0,
        outdoor_humidity=40.0,
        indoor_absolute_humidity=0.0,
        outdoor_absolute_humidity=0.0,
        absolute_humidity_delta=0.0,
        indoor_dew_point=0.0,
        outdoor_dew_point=0.0,
        reason=REASON_STRUCTURE_PROTECTION_ACTIVE,
        reason_detail=REASON_DETAIL_HUMIDITY_SPIKE,
        humidity_recommended=False,
        temperature_recommended=False,
        structure_protection_active=True,
        window_open=False,
    )

    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 22.0,
            "sensor.indoor_humidity": 56.0,
            "sensor.outdoor_temp": 20.0,
            "sensor.outdoor_humidity": 35.0,
        },
        options=options,
        previous_data=previous,
    )

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_EMPFOHLEN
    assert result.reason == REASON_STRUCTURE_PROTECTION_ACTIVE
    assert result.reason_detail == REASON_DETAIL_HUMIDITY_SPIKE


@pytest.mark.asyncio
async def test_min_structure_ventilation_duration_holds_recommendation() -> None:
    options = _default_options()
    options[CONF_MAX_INDOOR_HUMIDITY] = 90.0
    options[CONF_MAX_INDOOR_DEW_POINT_SPREAD] = 0.5
    options[CONF_HUMIDITY_SPIKE_THRESHOLD] = 99.0
    options[CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES] = 10

    previous = VentilationRecommendationData(
        recommendation=STATE_LUEFTEN_EMPFOHLEN,
        indoor_temperature=22.0,
        indoor_humidity=60.0,
        outdoor_temperature=20.0,
        outdoor_humidity=35.0,
        indoor_absolute_humidity=0.0,
        outdoor_absolute_humidity=0.0,
        absolute_humidity_delta=0.0,
        indoor_dew_point=0.0,
        outdoor_dew_point=0.0,
        reason=REASON_STRUCTURE_PROTECTION_ACTIVE,
        reason_detail=REASON_DETAIL_CRITICAL_HUMIDITY,
        humidity_recommended=False,
        temperature_recommended=False,
        structure_protection_active=True,
        window_open=False,
    )

    coordinator = _build_coordinator(
        states={
            "sensor.indoor_temp": 22.0,
            "sensor.indoor_humidity": 55.0,
            "sensor.outdoor_temp": 20.0,
            "sensor.outdoor_humidity": 30.0,
        },
        options=options,
        previous_data=previous,
    )
    coordinator._structure_protection_started_at = dt_util.utcnow() - timedelta(minutes=5)

    result = await coordinator._async_update_data()

    assert result.recommendation == STATE_LUEFTEN_EMPFOHLEN
    assert result.reason == REASON_STRUCTURE_PROTECTION_ACTIVE
    assert result.reason_detail == REASON_DETAIL_MIN_VENTILATION_DURATION
