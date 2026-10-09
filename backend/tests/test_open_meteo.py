import json

import httpx

from weather.open_meteo import FORECAST_URL, fetch_hourly_precipitation


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_normalizes_hourly_precipitation():
    payload = {
        "latitude": 19.1,
        "longitude": 72.9,
        "elevation": 10,
        "timezone": "GMT",
        "hourly_units": {"time": "iso8601", "precipitation": "mm"},
        "hourly": {
            "time": ["2026-10-09T12:00", "2026-10-09T13:00"],
            "precipitation": [0.2, None],
        },
    }

    def handler(request):
        assert request.url.host == "api.open-meteo.com"
        assert request.url.path == "/v1/forecast"
        assert request.url.params["hourly"] == "precipitation"
        assert request.url.params["timezone"] == "UTC"
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(
        19.076, 72.8777, client=make_client(handler)
    )

    assert result["status"] == "available"
    assert result["source_type"] == "weather_model_forecast"
    assert result["precipitation_unit"] == "mm"
    assert result["hours"][0]["precipitation_mm"] == 0.2
    assert result["hours"][1]["precipitation_mm"] is None
    assert result["provider_location"]["latitude"] == 19.1
    assert result["is_simulated"] is False


def test_http_failure_is_unavailable_not_zero():
    def handler(request):
        return httpx.Response(503, json={"reason": "temporarily unavailable"})

    result = fetch_hourly_precipitation(
        19.076, 72.8777, client=make_client(handler)
    )

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_HTTP_ERROR"
    assert result["hours"] == []


def test_missing_hourly_data_is_unavailable():
    def handler(request):
        return httpx.Response(200, json={"latitude": 19.0})

    result = fetch_hourly_precipitation(
        19.076, 72.8777, client=make_client(handler)
    )

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_MISSING_HOURLY_DATA"


def test_unexpected_units_are_rejected():
    payload = {
        "hourly_units": {"precipitation": "inch"},
        "hourly": {
            "time": ["2026-10-09T12:00"],
            "precipitation": [0.1],
        },
    }

    def handler(request):
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(
        19.076, 72.8777, client=make_client(handler)
    )

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_UNEXPECTED_PRECIPITATION_UNIT"


def test_mismatched_hourly_arrays_are_rejected():
    payload = {
        "hourly_units": {"precipitation": "mm"},
        "hourly": {
            "time": ["2026-10-09T12:00", "2026-10-09T13:00"],
            "precipitation": [0.1],
        },
    }

    def handler(request):
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(
        19.076, 72.8777, client=make_client(handler)
    )

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_INVALID_HOURLY_FIELDS"
