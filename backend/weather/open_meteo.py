"""Small Open-Meteo adapter for hourly precipitation forecasts.

This module fetches and normalizes provider data. It does not calculate flood
risk and does not claim that model output is a direct rain-gauge observation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT_SECONDS = 10.0


def _utc_now() -> str:
    """Return the current timestamp in ISO 8601 UTC format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_hourly_precipitation(
    latitude: float,
    longitude: float,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Fetch hourly precipitation forecast data for one coordinate.

    Returns a normalized dictionary with status='available' on success.
    Provider/network/validation problems return status='unavailable' with an
    error code; callers should not interpret failure as zero rainfall.

    The optional client argument is intended for deterministic tests.
    """
    retrieved_at = _utc_now()
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "precipitation",
        "forecast_days": 2,
        "timezone": "UTC",
    }

    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout)

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
    except ValueError:
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
    units = payload.get("hourly_units", {}).get("precipitation")

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
        if not isinstance(valid_time, str):
            return _unavailable(retrieved_at, "WEATHER_INVALID_TIMESTAMP")
        if amount is not None and (
            isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0
        ):
            return _unavailable(retrieved_at, "WEATHER_INVALID_PRECIPITATION_VALUE")

        normalized_hours.append(
            {
                "valid_at": valid_time,
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
