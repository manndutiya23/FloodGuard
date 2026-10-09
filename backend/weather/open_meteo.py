"""Validated Open-Meteo hourly precipitation adapter.

This module fetches and normalizes weather-model forecasts. It does not
calculate flood risk and does not represent model output as rain-gauge data.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT_SECONDS = 10.0


def _utc_now() -> str:
    """Return the current timestamp in ISO 8601 UTC format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _valid_coordinate(value: object, minimum: float, maximum: float) -> bool:
    """Return whether a coordinate is a finite, in-range real number."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and minimum <= value <= maximum
    )


def _normalize_valid_time(value: object) -> str | None:
    """Validate an hourly ISO timestamp and normalize it to UTC with Z.

    Open-Meteo is requested with timezone=UTC, so timestamps without an
    explicit offset are interpreted as UTC. Timestamps with offsets are
    converted to UTC. A malformed timestamp is not allowed into the pipeline.
    """
    if not isinstance(value, str) or "T" not in value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_hourly_precipitation(
    latitude: float,
    longitude: float,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch and normalize hourly precipitation for one coordinate.

    Returns status='available' only after the response shape, units, timestamps,
    and precipitation values pass validation. Provider or validation failures
    return status='unavailable'; they are never replaced with zero rainfall.

    The optional client argument supports deterministic tests using MockTransport.
    """
    retrieved_at = _utc_now()

    if not _valid_coordinate(latitude, -90.0, 90.0) or not _valid_coordinate(
        longitude, -180.0, 180.0
    ):
        return _unavailable(retrieved_at, "WEATHER_INVALID_LOCATION")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "precipitation",
        "forecast_days": 2,
        "timezone": "UTC",
    }

    owns_client = client is None
    http_client = client if client is not None else httpx.Client(timeout=timeout)

    try:
        response = http_client.get(FORECAST_URL, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException:
        return _unavailable(retrieved_at, "WEATHER_TIMEOUT")
    except httpx.HTTPStatusError:
        return _unavailable(retrieved_at, "WEATHER_HTTP_ERROR")
    except httpx.RequestError:
        return _unavailable(retrieved_at, "WEATHER_REQUEST_ERROR")
    except (ValueError, UnicodeError):
        return _unavailable(retrieved_at, "WEATHER_INVALID_JSON")
    finally:
        if owns_client:
            http_client.close()

    if not isinstance(payload, dict):
        return _unavailable(retrieved_at, "WEATHER_INVALID_RESPONSE")

    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return _unavailable(retrieved_at, "WEATHER_MISSING_HOURLY_DATA")

    times = hourly.get("time")
    precipitation = hourly.get("precipitation")
    hourly_units = payload.get("hourly_units")
    units = hourly_units.get("precipitation") if isinstance(hourly_units, dict) else None

    if (
        not isinstance(times, list)
        or not isinstance(precipitation, list)
        or len(times) == 0
        or len(times) != len(precipitation)
        or not isinstance(units, str)
    ):
        return _unavailable(retrieved_at, "WEATHER_INVALID_HOURLY_FIELDS")

    if units != "mm":
        return _unavailable(retrieved_at, "WEATHER_UNEXPECTED_PRECIPITATION_UNIT")

    normalized_hours: list[dict[str, Any]] = []
    for valid_time, amount in zip(times, precipitation):
        normalized_time = _normalize_valid_time(valid_time)
        if normalized_time is None:
            return _unavailable(retrieved_at, "WEATHER_INVALID_TIMESTAMP")

        if amount is not None and (
            isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or not math.isfinite(amount)
            or amount < 0
        ):
            return _unavailable(retrieved_at, "WEATHER_INVALID_PRECIPITATION_VALUE")

        normalized_hours.append(
            {
                "forecast_valid_at": normalized_time,
                "precipitation_mm": float(amount) if amount is not None else None,
            }
        )

    return {
        "source": "Open-Meteo",
        "source_type": "weather_model_forecast",
        "status": "available",
        "is_simulated": False,
        "requested_location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "provider_location": {
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "elevation_m": payload.get("elevation"),
        },
        "timezone": payload.get("timezone", "UTC"),
        "precipitation_unit": units,
        "retrieved_at": retrieved_at,
        "hours": normalized_hours,
    }


def _unavailable(retrieved_at: str, error_code: str) -> dict[str, Any]:
    """Return a safe failure shape; never turn failure into zero rainfall."""
    return {
        "source": "Open-Meteo",
        "source_type": "weather_model_forecast",
        "status": "unavailable",
        "is_simulated": False,
        "retrieved_at": retrieved_at,
        "hours": [],
        "error_code": error_code,
    }
