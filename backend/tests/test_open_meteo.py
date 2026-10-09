import json

import httpx
import pytest

from weather.open_meteo import FORECAST_URL, fetch_hourly_precipitation


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def make_payload(*, times=None, precipitation=None, units="mm"):
    return {
        "latitude": 19.1,
        "longitude": 72.9,
        "elevation": 10,
        "timezone": "GMT",
        "hourly_units": {"time": "iso8601", "precipitation": units},
        "hourly": {
            "time": times if times is not None else ["2026-10-09T12:00", "2026-10-09T13:00"],
            "precipitation": precipitation if precipitation is not None else [0.2, None],
        },
    }


def test_normalizes_hourly_precipitation_and_timestamps():
    payload = make_payload()

    def handler(request):
        assert request.url == httpx.URL(FORECAST_URL).copy_with(params={
            "latitude": "19.076",
            "longitude": "72.8777",
            "hourly": "precipitation",
            "forecast_days": "2",
            "timezone": "UTC",
        })
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "available"
    assert result["source_type"] == "weather_model_forecast"
    assert result["precipitation_unit"] == "mm"
    assert result["hours"][0]["precipitation_mm"] == 0.2
    assert result["hours"][0]["forecast_valid_at"] == "2026-10-09T12:00:00Z"
    assert result["hours"][1]["precipitation_mm"] is None
    assert result["provider_location"]["latitude"] == 19.1
    assert result["is_simulated"] is False
    assert result["retrieved_at"].endswith("Z")


def test_http_failure_is_unavailable_not_zero():
    def handler(request):
        return httpx.Response(503, json={"reason": "temporarily unavailable"})

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_HTTP_ERROR"
    assert result["hours"] == []


def test_missing_hourly_data_is_unavailable():
    def handler(request):
        return httpx.Response(200, json={"latitude": 19.0})

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_MISSING_HOURLY_DATA"


def test_unexpected_units_are_rejected():
    payload = make_payload(units="inch")

    def handler(request):
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_UNEXPECTED_PRECIPITATION_UNIT"


def test_mismatched_hourly_arrays_are_rejected():
    payload = make_payload(
        times=["2026-10-09T12:00", "2026-10-09T13:00"],
        precipitation=[0.1],
    )

    def handler(request):
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_INVALID_HOURLY_FIELDS"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -0.1, True, "0.2"])
def test_invalid_precipitation_values_are_rejected(value):
    payload = make_payload(precipitation=[value, 0.1])

    def handler(request):
        # Raw content lets the test exercise non-finite JSON-like values. The
        # standard JSON encoder used by httpx's `json=` parameter rejects NaN/Inf
        # before the adapter receives the response.
        return httpx.Response(
            200,
            content=json.dumps(payload, allow_nan=True).encode("utf-8"),
            headers={"content-type": "application/json"},
        )

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_INVALID_PRECIPITATION_VALUE"
    assert result["hours"] == []


@pytest.mark.parametrize("timestamp", ["not-a-timestamp", "2026-10-09", ""])
def test_invalid_hourly_timestamps_are_rejected(timestamp):
    payload = make_payload(times=[timestamp], precipitation=[0.1])

    def handler(request):
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_INVALID_TIMESTAMP"


def test_invalid_hourly_units_container_does_not_crash():
    payload = make_payload()
    payload["hourly_units"] = None

    def handler(request):
        return httpx.Response(200, json=payload)

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_INVALID_HOURLY_FIELDS"


@pytest.mark.parametrize(
    "latitude,longitude",
    [(91.0, 72.8777), (-91.0, 72.8777), (19.076, 181.0), (float("nan"), 72.8777)],
)
def test_invalid_coordinates_are_rejected_before_request(latitude, longitude):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=make_payload())

    result = fetch_hourly_precipitation(latitude, longitude, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_INVALID_LOCATION"
    assert calls == []


def test_timeout_is_reported_as_unavailable():
    def handler(request):
        raise httpx.ReadTimeout("test timeout", request=request)

    result = fetch_hourly_precipitation(19.076, 72.8777, client=make_client(handler))

    assert result["status"] == "unavailable"
    assert result["error_code"] == "WEATHER_TIMEOUT"
    assert result["hours"] == []
