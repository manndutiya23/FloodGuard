"""FloodGuard API: reference data, weather metadata, and prototype risk index."""
from __future__ import annotations

import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from risk_engine import assess_risk
from weather.open_meteo import fetch_hourly_precipitation

app = FastAPI(
    title="FloodGuard API",
    description="API for Mumbai hyperlocal flood intelligence.",
    version="0.3.0",
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WARD_CSV_PATH = REPOSITORY_ROOT / "data" / "reference" / "floodguard_mumbai_ward_flood_exposure.csv"

# This is one representative weather point, not an independent estimate for each ward.
MUMBAI_REFERENCE_LOCATION = {"latitude": 19.0760, "longitude": 72.8777}
WEATHER_LOCATION_SCOPE = (
    "Representative Mumbai point only; this weather signal is not ward-specific. "
    "Do not interpret results as independently measured conditions in each ward."
)


def _read_wards() -> list[dict[str, Any]]:
    """Read reference CSV while preserving source field names and provenance."""
    try:
        with WARD_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Historical ward reference data could not be loaded.") from exc

    wards: list[dict[str, Any]] = []
    for row in rows:
        try:
            row["population_potentially_exposed_within_250m_buffer"] = int(
                row["population_potentially_exposed_within_250m_buffer"]
            )
            row["percentage_of_ward_population_potentially_exposed_percent"] = float(
                row["percentage_of_ward_population_potentially_exposed_percent"]
            )
            row["source_page"] = int(row["source_page"])
            row["underlying_population_data_year"] = int(row["underlying_population_data_year"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=500, detail="Historical ward reference data contains invalid fields.") from exc
        wards.append(row)
    return wards


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_precipitation(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _forecast_signal(
    weather: dict[str, Any], evaluated_at: datetime | None = None
) -> dict[str, Any] | None:
    """Aggregate exactly three consecutive future hourly values or return None.

    When evaluated exactly on the hour, that hour is still eligible. At any
    later instant within the hour, use the next whole hour to avoid scoring a
    forecast period that has already started/partly elapsed. The end timestamp
    is exclusive. Missing values are not skipped or replaced with zero.
    """
    if weather.get("status") != "available":
        return None

    retrieved_at = _parse_time(weather.get("retrieved_at"))
    if retrieved_at is None:
        return None
    now = evaluated_at or _utc_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    if retrieved_at > now:
        return None

    floor_hour = now.replace(minute=0, second=0, microsecond=0)
    window_start = floor_hour if now == floor_hour else floor_hour + timedelta(hours=1)
    required_times = [window_start + timedelta(hours=offset) for offset in range(3)]

    hours = weather.get("hours")
    if not isinstance(hours, list):
        return None

    values_by_time: dict[datetime, object] = {}
    for hour in hours:
        if not isinstance(hour, dict):
            continue
        valid_at = _parse_time(hour.get("forecast_valid_at"))
        if valid_at is None:
            continue
        # Duplicate timestamps are ambiguous; refuse to make a score from them.
        if valid_at in values_by_time:
            return None
        values_by_time[valid_at] = hour.get("precipitation_mm")

    amounts: list[float] = []
    for required_time in required_times:
        amount = values_by_time.get(required_time)
        if not _is_precipitation(amount):
            return None
        amounts.append(float(amount))

    window_end = window_start + timedelta(hours=3)
    return {
        "kind": "forecast",
        "value": round(sum(amounts), 2),
        "unit": "mm",
        "period_minutes": 180,
        "forecast_window_start": _iso_utc(window_start),
        "forecast_window_end": _iso_utc(window_end),
        "retrieved_at": _iso_utc(retrieved_at),
        "source": weather.get("source", "Open-Meteo"),
        "status": "simulated" if weather.get("is_simulated", False) else "available",
        "is_simulated": bool(weather.get("is_simulated", False)),
    }


def _latest_usable_info(weather: dict[str, Any], evaluated_at: datetime) -> dict[str, Any] | None:
    """Return a single source-backed hourly value, never a substitute risk score.

    Prefer the most recent valid-time forecast point at/before evaluation time;
    if none exists, use the nearest upcoming usable point. The original forecast
    timestamp and retrieval timestamp remain separate. The age field measures
    time since retrieval, not time since forecast validity.
    """
    if weather.get("status") != "available":
        return None
    retrieved_at = _parse_time(weather.get("retrieved_at"))
    if retrieved_at is None or retrieved_at > evaluated_at:
        return None
    retrieval_age_minutes = int((evaluated_at - retrieved_at).total_seconds() // 60)

    candidates: list[tuple[datetime, float]] = []
    hours = weather.get("hours")
    if not isinstance(hours, list):
        return None
    for hour in hours:
        if not isinstance(hour, dict):
            continue
        valid_at = _parse_time(hour.get("forecast_valid_at"))
        amount = hour.get("precipitation_mm")
        if valid_at is None or not _is_precipitation(amount):
            continue
        candidates.append((valid_at, float(amount)))
    if not candidates:
        return None

    past_or_current = [item for item in candidates if item[0] <= evaluated_at]
    if past_or_current:
        valid_at, amount = max(past_or_current, key=lambda item: item[0])
    else:
        valid_at, amount = min(candidates, key=lambda item: item[0])

    return {
        "kind": "forecast",
        "precipitation_mm": amount,
        "unit": "mm",
        "forecast_valid_at": _iso_utc(valid_at),
        "retrieved_at": _iso_utc(retrieved_at) if retrieved_at else None,
        "retrieval_age_minutes": retrieval_age_minutes,
        "age_definition": "minutes since retrieved_at; not time since forecast_valid_at",
        "source": weather.get("source", "Open-Meteo"),
        "is_simulated": bool(weather.get("is_simulated", False)),
    }


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "floodguard-api"}


@app.get("/wards", tags=["reference data"])
def get_wards() -> dict[str, Any]:
    return {
        "data": _read_wards(),
        "meta": {
            "data_type": "historical_vulnerability_baseline",
            "source": "Mumbai Climate Action Plan - Climate & Air Pollution Risks and Vulnerability Assessment",
            "source_page": 112,
            "underlying_population_data_year": 2011,
        },
    }


@app.get("/weather", tags=["environmental data"])
def get_weather() -> dict[str, Any]:
    weather = fetch_hourly_precipitation(**MUMBAI_REFERENCE_LOCATION)
    weather["location_scope"] = WEATHER_LOCATION_SCOPE
    if weather.get("status") == "unavailable":
        weather["message"] = "Weather data is currently unavailable; no zero-rainfall value was substituted."
    return {"data": weather}


@app.get("/risk", tags=["risk assessment"])
def get_risk(
    ward_code: str | None = Query(default=None, description="Optional source ward code, e.g. F/N"),
) -> dict[str, Any]:
    wards = _read_wards()
    if ward_code is not None:
        selected = [ward for ward in wards if ward["ward_code"].casefold() == ward_code.casefold()]
        if not selected:
            raise HTTPException(status_code=400, detail="Unknown ward_code. Use a code from GET /wards.")
        wards = selected

    weather = fetch_hourly_precipitation(**MUMBAI_REFERENCE_LOCATION)
    evaluated_at = _utc_now()
    signal = _forecast_signal(weather, evaluated_at)
    latest_info = _latest_usable_info(weather, evaluated_at) if signal is None else None
    results: list[dict[str, Any]] = []

    for ward in wards:
        rainfall_input: dict[str, Any]
        if signal is not None:
            rainfall_input = signal
        elif weather.get("status") == "available":
            rainfall_input = {
                "status": "unavailable",
                "is_simulated": bool(weather.get("is_simulated", False)),
                "error_code": "INCOMPLETE_FORECAST_WINDOW",
            }
        else:
            rainfall_input = {
                "status": weather.get("status", "unavailable"),
                "is_simulated": bool(weather.get("is_simulated", False)),
                "error_code": weather.get("error_code"),
            }

        assessment = assess_risk(
            ward=ward,
            rainfall=rainfall_input,
            reports=None,  # Report storage/integration is not implemented yet.
            evaluated_at=_iso_utc(evaluated_at),
        )
        assessment["location_scope"] = WEATHER_LOCATION_SCOPE
        assessment["weather_source"] = weather.get("source", "Open-Meteo")
        assessment["weather_source_type"] = weather.get("source_type", "weather_model_forecast")
        assessment["weather_status"] = weather.get("status", "unavailable")
        assessment["latest_available_info"] = latest_info
        if signal is None and weather.get("status") == "available":
            assessment["reasons"].append(
                "Latest usable forecast context, if present, is shown separately and is not a newly calculated score."
            )
        elif weather.get("status") == "unavailable":
            assessment["reasons"].append("Open-Meteo could not provide weather data for this request.")
        results.append(assessment)

    if signal is None:
        data_mode = "current_risk_unavailable"
    elif signal.get("is_simulated"):
        data_mode = "simulation"
    else:
        data_mode = "live_weather_with_historical_baseline"

    return {
        "data": results,
        "meta": {
            "risk_method": "heuristic-v0.2",
            "data_mode": data_mode,
            "location_scope": WEATHER_LOCATION_SCOPE,
            "important_limit": (
                "Prototype only; one representative point is used for all selected wards. "
                "This is not a ward-specific flood prediction or emergency warning. "
                "Citizen-report storage and live report integration are not implemented."
            ),
        },
    }
