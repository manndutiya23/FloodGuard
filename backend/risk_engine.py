"""Pure, explainable prototype risk scoring.

This is a heuristic signal, not a calibrated flood probability or an official
warning. The caller must ensure the rainfall coordinate is relevant to the
ward/location being assessed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_time(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _level(score: int) -> str:
    if score < 30:
        return "low"
    if score < 60:
        return "moderate"
    return "high"


def assess_risk(
    *,
    ward: dict[str, Any] | None,
    rainfall: dict[str, Any] | None,
    reports: list[dict[str, Any]] | None = None,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """Assess a ward only when usable forecast/observation input is present.

    Scoring v0.1:
    - Rainfall signal: 0-70 points from the accumulated precipitation over
      the supplied period, normalized to 30 mm.
    - Historical exposure context: 0-20 points from the source percentage.
    - Recent reports: 0-10 points for relevant reports in the last 6 hours;
      verified reports contribute more than unverified reports.

    Rainfall is required for a score. Historical exposure alone never creates
    a current-risk score. Caller supplies one rainfall amount and its period.
    """
    now = _parse_time(evaluated_at) if evaluated_at else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    calculated_at = now.isoformat().replace("+00:00", "Z")

    ward_code = ward.get("ward_code") if ward else None
    rainfall_status = (rainfall or {}).get("status", "unavailable")
    baseline_status = "available" if ward else "unavailable"
    report_list = reports or []
    reports_status = "available" if reports is not None else "unavailable"
    simulated = bool((rainfall or {}).get("is_simulated", False)) or any(
        bool(report.get("is_simulated")) for report in report_list
    )

    base = {
        "ward_code": ward_code,
        "risk_score": None,
        "risk_level": "unknown",
        "reasons": [],
        "data_status": {
            "rainfall": rainfall_status if rainfall_status in {"available", "unavailable", "stale", "simulated"} else "unavailable",
            "historical_baseline": baseline_status,
            "reports": reports_status,
        },
        "calculated_at": calculated_at,
        "is_simulated": simulated,
        "method": "heuristic-v0.1",
    }

    if rainfall_status != "available":
        base["reasons"].append("A current weather input is unavailable or not accepted; current risk cannot be assessed.")
        return base

    value = (rainfall or {}).get("value")
    unit = (rainfall or {}).get("unit")
    period_minutes = (rainfall or {}).get("period_minutes")
    kind = (rainfall or {}).get("kind")
    timestamp = (rainfall or {}).get("timestamp")

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value < 0
        or unit != "mm"
        or isinstance(period_minutes, bool)
        or not isinstance(period_minutes, int)
        or period_minutes <= 0
        or kind not in {"observation", "forecast"}
        or not isinstance(timestamp, str)
        or _parse_time(timestamp) is None
    ):
        base["data_status"]["rainfall"] = "unavailable"
        base["reasons"].append("Weather input failed validation; current risk cannot be assessed.")
        return base

    weather_time = _parse_time(timestamp)
    age_minutes = (now - weather_time).total_seconds() / 60 if weather_time else float("inf")
    # Forecast timestamps are valid-time stamps, not retrieval times. Freshness
    # is therefore checked by the caller/adapter; this check only guards
    # observations from being older than 3 hours.
    if kind == "observation" and age_minutes > 180:
        base["data_status"]["rainfall"] = "stale"
        base["reasons"].append("Rainfall observation is older than the prototype's 3-hour freshness limit.")
        return base

    rainfall_points = min(70.0, (float(value) / 30.0) * 70.0)
    exposure_pct = None
    if ward:
        raw_exposure = ward.get("percentage_of_ward_population_potentially_exposed_percent")
        if raw_exposure is None:
            raw_exposure = ward.get("percentage_of_ward_population_potentially_exposed_percent")
        if isinstance(raw_exposure, (int, float)) and not isinstance(raw_exposure, bool):
            exposure_pct = max(0.0, min(100.0, float(raw_exposure)))
    exposure_points = (exposure_pct / 100.0) * 20.0 if exposure_pct is not None else 0.0

    recent_report_points = 0.0
    for report in report_list:
        reported_at = _parse_time(report.get("reported_at", ""))
        if not reported_at or (now - reported_at).total_seconds() > 6 * 3600:
            continue
        if reported_at > now:
            continue
        recent_report_points += 6.0 if report.get("verification_status") == "verified" else 2.0
    recent_report_points = min(10.0, recent_report_points)

    score = max(0, min(100, round(rainfall_points + exposure_points + recent_report_points)))
    reasons = [
        f"{'Forecast' if kind == 'forecast' else 'Observed'} precipitation input: {float(value):g} mm over {period_minutes} minutes."
    ]
    if exposure_pct is not None:
        reasons.append(f"Historical exposure baseline contributes context ({exposure_pct:g}% of ward population in the source assessment; underlying population data year 2011).")
    else:
        reasons.append("No historical ward exposure baseline was supplied; score uses the weather signal and eligible reports only.")
    if recent_report_points:
        reasons.append("Recent incident reports contribute to the heuristic; unverified reports are not treated as confirmed incidents.")
    if kind == "forecast":
        reasons.append("This is a forecast-based heuristic signal, not confirmation of flooding or a calibrated flood probability.")

    base.update({
        "risk_score": score,
        "risk_level": _level(score),
        "reasons": reasons,
    })
    base["data_status"]["rainfall"] = "simulated" if (rainfall or {}).get("is_simulated") else "available"
    if simulated:
        base["is_simulated"] = True
    return base
