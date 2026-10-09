"""FloodGuard API application.

Initial local API with a historical ward endpoint, weather adapter endpoint,
and a clearly qualified prototype heuristic risk endpoint.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from risk_engine import assess_risk
from weather.open_meteo import fetch_hourly_precipitation

app = FastAPI(
    title="FloodGuard API",
    description="API for Mumbai hyperlocal flood intelligence.",
    version="0.2.0",
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WARD_CSV_PATH = REPOSITORY_ROOT / "data" / "reference" / "floodguard_mumbai_ward_flood_exposure.csv"

# One documented representative point is used only for the first integration
# slice. It is NOT a separate rainfall estimate for every ward.
MUMBAI_REFERENCE_LOCATION = {"latitude": 19.0760, "longitude": 72.8777}
WEATHER_LOCATION_SCOPE = (
    "Representative Mumbai point only; this weather signal is not ward-specific. "
    "Do not interpret results as independently measured conditions in each ward."
)


def _read_wards() -> list[dict[str, Any]]:
    """Read the source CSV while preserving its field names and provenance."""
    try:
        with WARD_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Historical ward reference data could not be loaded.",
        ) from exc

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
            row["underlying_population_data_year"] = int(
                row["underlying_population_data_year"]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=500,
                detail="Historical ward reference data contains invalid fields.",
            ) from exc
        wards.append(row)
    return wards


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _forecast_signal(weather: dict[str, Any]) -> dict[str, Any] | None:
    """Sum the next six forecast hours, using UTC valid-time labels."""
    if weather.get("status") != "available":
        return None

    now = _utc_now()
    hours = weather.get("hours", [])
    parsed: list[tuple[datetime, float]] = []
    for hour in hours:
        try:
            valid_at = datetime.fromisoformat(hour["valid_at"].replace("Z", "+00:00"))
            if valid_at.tzinfo is None:
                valid_at = valid_at.replace(tzinfo=timezone.utc)
            amount = hour["precipitation_mm"]
            if amount is None:
                continue
            parsed.append((valid_at.astimezone(timezone.utc), float(amount)))
        except (KeyError, TypeError, ValueError):
            continue

    future_hours = sorted(
        [(valid_at, amount) for valid_at, amount in parsed if now <= valid_at < now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=7)],
        key=lambda item: item[0],
    )[:6]

    if len(future_hours) < 3:
        return None

    return {
        "kind": "forecast",
        "value": round(sum(amount for _, amount in future_hours), 2),
        "unit": "mm",
        "period_minutes": len(future_hours) * 60,
        "timestamp": future_hours[0][0].isoformat().replace("+00:00", "Z"),
        "source": weather.get("source", "Open-Meteo"),
        "status": "available",
        "is_simulated": False,
    }


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is responding."""
    return {"status": "ok", "service": "floodguard-api"}


@app.get("/wards", tags=["reference data"])
def get_wards() -> dict[str, Any]:
    """Return historical ward exposure values and source provenance."""
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
    """Fetch normalized hourly forecast data for the representative Mumbai point."""
    weather = fetch_hourly_precipitation(**MUMBAI_REFERENCE_LOCATION)
    weather["location_scope"] = WEATHER_LOCATION_SCOPE
    if weather.get("status") == "unavailable":
        # Keep the endpoint usable so the frontend can display source failure
        # as data, not mistake it for an API process failure.
        weather["message"] = "Weather data is currently unavailable; no zero-rainfall value was substituted."
    return {"data": weather}


@app.get("/risk", tags=["risk assessment"])
def get_risk(
    ward_code: str | None = Query(default=None, description="Optional source ward code, e.g. F/N"),
) -> dict[str, Any]:
    """Return prototype heuristic assessments with explicit geographic caveats."""
    wards = _read_wards()
    if ward_code is not None:
        selected = [ward for ward in wards if ward["ward_code"].casefold() == ward_code.casefold()]
        if not selected:
            raise HTTPException(status_code=400, detail="Unknown ward_code. Use a code from GET /wards.")
        wards = selected

    weather = fetch_hourly_precipitation(**MUMBAI_REFERENCE_LOCATION)
    signal = _forecast_signal(weather)
    results = []
    for ward in wards:
        assessment = assess_risk(
            ward=ward,
            rainfall=(
                {**signal, "is_simulated": False}
                if signal is not None
                else {"status": "unavailable", "is_simulated": False}
            ),
            reports=None,  # Report storage is not implemented yet.
            evaluated_at=_utc_now().isoformat().replace("+00:00", "Z"),
        )
        assessment["location_scope"] = WEATHER_LOCATION_SCOPE
        assessment["weather_source"] = "Open-Meteo"
        assessment["weather_source_type"] = "weather_model_forecast"
        assessment["weather_status"] = weather.get("status", "unavailable")
        if weather.get("status") == "unavailable":
            assessment["reasons"].append("Open-Meteo could not provide weather data for this request.")
        results.append(assessment)

    return {
        "data": results,
        "meta": {
            "risk_method": "heuristic-v0.1",
            "data_mode": "live_weather_with_historical_baseline" if signal is not None else "current_risk_unavailable",
            "location_scope": WEATHER_LOCATION_SCOPE,
            "important_limit": "Prototype only; one representative point is used for all selected wards. This is not a ward-specific flood prediction or emergency warning.",
        },
    }
