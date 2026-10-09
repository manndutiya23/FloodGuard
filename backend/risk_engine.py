"""Explainable prototype risk index for FloodGuard.

This module is a deterministic heuristic, not a calibrated flood probability,
confirmed flood observation, or official warning. Inputs are collected and
validated by the caller; this module does not perform network or database I/O.

Provisional configuration is documented in docs/RISK_SCORING_DECISIONS.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

@dataclass(frozen=True)
class RiskScoringConfig:
    """Configurable prototype assumptions; defaults are documented separately."""

    max_rainfall_points: float = 70.0
    max_exposure_points: float = 20.0
    max_report_points: float = 10.0
    maximum_total_points: int = 100
    rainfall_normalization_mm: float = 30.0
    observation_freshness_minutes: int = 180
    forecast_window_minutes: int = 180
    report_eligibility_minutes: int = 120
    verified_report_base_points: float = 6.0
    unverified_report_base_points: float = 2.0
    report_duplicate_distance_meters: float = 200.0
    report_duplicate_time_minutes: int = 30
    low_to_moderate_threshold: int = 30
    moderate_to_high_threshold: int = 60

    def __post_init__(self) -> None:
        if self.maximum_total_points != 100:
            raise ValueError("The prototype risk index maximum is fixed at 100 points.")
        if abs(self.max_rainfall_points + self.max_exposure_points + self.max_report_points - 100.0) > 1e-9:
            raise ValueError("Component maxima must sum to the fixed 100-point total.")
        if self.rainfall_normalization_mm <= 0 or self.forecast_window_minutes <= 0:
            raise ValueError("Rainfall normalization and forecast window must be positive.")
        if self.observation_freshness_minutes < 0 or self.report_eligibility_minutes <= 0:
            raise ValueError("Freshness and eligibility windows must be non-negative/positive.")
        if self.report_duplicate_distance_meters < 0 or self.report_duplicate_time_minutes < 0:
            raise ValueError("Duplicate-detection thresholds cannot be negative.")


DEFAULT_CONFIG = RiskScoringConfig()
METHOD_VERSION = "heuristic-v0.2"


def _parse_time(value: object) -> datetime | None:
    """Parse ISO 8601 and normalize to UTC; timezone-naive values are treated as UTC."""
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


def _level(score: int, config: RiskScoringConfig = DEFAULT_CONFIG) -> str:
    """Apply current provisional display thresholds."""
    if score < config.low_to_moderate_threshold:
        return "low"
    if score < config.moderate_to_high_threshold:
        return "moderate"
    return "high"


def _valid_amount(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _rainfall_validation(
    rainfall: dict[str, Any], now: datetime, config: RiskScoringConfig
) -> tuple[str, str | None, datetime | None, datetime | None]:
    """Return (status, reason, start, end) for an observation or forecast signal."""
    status = rainfall.get("status", "unavailable")
    simulated = bool(rainfall.get("is_simulated", False)) or status == "simulated"
    if status not in {"available", "simulated"}:
        if status == "stale":
            return "stale", "The rainfall input is marked stale; current risk cannot be assessed.", None, None
        if rainfall.get("error_code") == "INCOMPLETE_FORECAST_WINDOW":
            return "unavailable", "A complete three-hour future forecast window is unavailable; current risk cannot be assessed.", None, None
        return "unavailable", "Weather data is unavailable; current risk cannot be assessed.", None, None

    value = rainfall.get("value")
    unit = rainfall.get("unit")
    period = rainfall.get("period_minutes")
    kind = rainfall.get("kind")
    retrieved_at = _parse_time(rainfall.get("retrieved_at"))
    if (
        not _valid_amount(value)
        or unit != "mm"
        or isinstance(period, bool)
        or not isinstance(period, int)
        or period <= 0
        or kind not in {"observation", "forecast"}
        or retrieved_at is None
    ):
        return "unavailable", "Weather input failed validation; current risk cannot be assessed.", None, None

    # A retrieved timestamp may not credibly be ahead of the evaluation clock.
    if retrieved_at > now:
        return "unavailable", "Weather retrieval timestamp is in the future; current risk cannot be assessed.", None, None

    if kind == "observation":
        observed_at = _parse_time(rainfall.get("observed_at"))
        if observed_at is None:
            return "unavailable", "Observation timestamp is missing or invalid; current risk cannot be assessed.", None, None
        age_minutes = (now - observed_at).total_seconds() / 60.0
        if age_minutes < 0:
            return "unavailable", "Rainfall observation timestamp is in the future; current risk cannot be assessed.", None, None
        if age_minutes > config.observation_freshness_minutes:
            return "stale", f"Rainfall observation is older than the provisional {config.observation_freshness_minutes}-minute freshness limit.", None, None
        return ("simulated" if simulated else "available"), None, observed_at, None

    # Forecast scoring uses a pre-aggregated, exact three-hour half-open window.
    window_start = _parse_time(rainfall.get("forecast_window_start"))
    window_end = _parse_time(rainfall.get("forecast_window_end"))
    if window_start is None or window_end is None:
        return "unavailable", "Forecast window timestamps are missing or invalid; current risk cannot be assessed.", None, None

    if window_end <= now:
        return "stale", "The entire three-hour forecast window has elapsed; current risk cannot be assessed from it.", window_start, window_end
    if window_start < now:
        return "unavailable", "The forecast window overlaps elapsed time and cannot be used for a new score.", window_start, window_end
    if window_end - window_start != timedelta(minutes=config.forecast_window_minutes) or period != config.forecast_window_minutes:
        return "unavailable", f"Forecast scoring requires exactly {config.forecast_window_minutes} minutes.", window_start, window_end

    return ("simulated" if simulated else "available"), None, window_start, window_end


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance between two latitude/longitude points."""
    earth_radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * earth_radius_m * math.asin(min(1.0, math.sqrt(a)))


def _valid_lat_lon(report: dict[str, Any]) -> tuple[float, float] | None:
    lat = report.get("latitude")
    lon = report.get("longitude")
    if (
        isinstance(lat, bool)
        or isinstance(lon, bool)
        or not isinstance(lat, (int, float))
        or not isinstance(lon, (int, float))
        or not math.isfinite(lat)
        or not math.isfinite(lon)
        or not -90 <= lat <= 90
        or not -180 <= lon <= 180
    ):
        return None
    return float(lat), float(lon)


def _candidate_duplicate(a: dict[str, Any], b: dict[str, Any], config: RiskScoringConfig) -> bool:
    """Provisional duplicate candidate check; never deletes or edits source reports."""
    # Reports with explicit shared grouping metadata are treated as one scoring group.
    a_group = a.get("duplicate_group_id")
    b_group = b.get("duplicate_group_id")
    if a_group is not None and b_group is not None and str(a_group) == str(b_group):
        return True

    # Same report ID should never score twice if the caller accidentally repeats it.
    a_id = a.get("report_id")
    b_id = b.get("report_id")
    if a_id is not None and b_id is not None and str(a_id) == str(b_id):
        return True

    loc_a = _valid_lat_lon(a)
    loc_b = _valid_lat_lon(b)
    time_a = _parse_time(a.get("reported_at"))
    time_b = _parse_time(b.get("reported_at"))
    if loc_a is None or loc_b is None or time_a is None or time_b is None:
        return False

    if abs((time_a - time_b).total_seconds()) > config.report_duplicate_time_minutes * 60:
        return False
    if _haversine_meters(*loc_a, *loc_b) > config.report_duplicate_distance_meters:
        return False

    category_a = str(a.get("category", "")).strip().casefold()
    category_b = str(b.get("category", "")).strip().casefold()
    if category_a and category_b and category_a != category_b:
        return False

    ward_a = a.get("ward_code")
    ward_b = b.get("ward_code")
    if ward_a and ward_b and str(ward_a).casefold() != str(ward_b).casefold():
        return False
    return True


def _report_points(
    reports: list[dict[str, Any]], *, ward_code: str | None, now: datetime, config: RiskScoringConfig
) -> tuple[float, bool, int]:
    """Calculate a decaying contribution capped at ten points.

    Likely duplicate reports are grouped for scoring but the input list is never
    modified. Each group contributes only its strongest individual contribution.
    Proximity/time matches are candidate duplicates for review, not proof that
    the reports describe the same incident.
    """
    eligible: list[tuple[dict[str, Any], datetime, float]] = []
    has_simulated = any(isinstance(report, dict) and bool(report.get("is_simulated")) for report in reports)

    for report in reports:
        if not isinstance(report, dict):
            continue
        # A resolved workflow report is no longer treated as a current incident.
        if str(report.get("status", "new")).casefold() == "resolved":
            continue
        report_ward = report.get("ward_code")
        # No ward geometry is wired into this pure module yet. For a ward-specific
        # assessment require explicit upstream ward association; never guess it.
        if ward_code and (not report_ward or str(report_ward).casefold() != ward_code.casefold()):
            continue
        reported_at = _parse_time(report.get("reported_at"))
        if reported_at is None:
            continue
        age_minutes = (now - reported_at).total_seconds() / 60.0
        if age_minutes < 0 or age_minutes >= config.report_eligibility_minutes:
            continue
        verification = report.get("verification_status")
        base_points = (
            config.verified_report_base_points
            if verification == "verified"
            else config.unverified_report_base_points
        )
        decay = max(0.0, 1.0 - age_minutes / config.report_eligibility_minutes)
        contribution = base_points * decay
        if contribution > 0:
            eligible.append((report, reported_at, contribution))

    # Greedy, deterministic complete-link grouping. A candidate has to meet the
    # spatial/time threshold against every member in a group, limiting chain merges.
    eligible.sort(key=lambda entry: (entry[1], str(entry[0].get("report_id", ""))))
    groups: list[list[tuple[dict[str, Any], datetime, float]]] = []
    for entry in eligible:
        placed = False
        for group in groups:
            if all(_candidate_duplicate(entry[0], member[0], config) for member in group):
                group.append(entry)
                placed = True
                break
        if not placed:
            groups.append([entry])

    points = sum(max(member[2] for member in group) for group in groups)
    return min(config.max_report_points, points), has_simulated, len(groups)


def assess_risk(
    *,
    ward: dict[str, Any] | None,
    rainfall: dict[str, Any] | None,
    reports: list[dict[str, Any]] | None = None,
    evaluated_at: str | None = None,
    config: RiskScoringConfig | None = None,
) -> dict[str, Any]:
    """Assess a ward using the current documented prototype heuristic.

    Rainfall is mandatory for a new score. If it is missing, invalid, stale, or
    an incomplete forecast window, the response is unknown rather than low.
    The caller may separately expose latest usable weather context; this function
    deliberately does not confuse that context with a score.
    """
    config = config or DEFAULT_CONFIG
    now = _parse_time(evaluated_at) if evaluated_at else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    calculated_at = _iso_utc(now)
    ward_code = ward.get("ward_code") if isinstance(ward, dict) else None

    report_list = reports if reports is not None else []
    reports_status = "unavailable" if reports is None else "available"
    reports_simulated = any(
        isinstance(report, dict) and bool(report.get("is_simulated"))
        for report in report_list
    )
    rainfall_input = rainfall if isinstance(rainfall, dict) else {}
    rainfall_is_simulated = bool(rainfall_input.get("is_simulated", False)) or rainfall_input.get("status") == "simulated"
    any_simulated = rainfall_is_simulated or reports_simulated

    base: dict[str, Any] = {
        "ward_code": ward_code,
        "risk_score": None,
        "risk_level": "unknown",
        "reasons": [],
        "data_status": {
            "rainfall": "unavailable",
            "historical_baseline": "available" if isinstance(ward, dict) else "unavailable",
            "reports": "simulated" if reports_simulated else reports_status,
        },
        "calculated_at": calculated_at,
        "is_simulated": any_simulated,
        "method": METHOD_VERSION,
        "score_components": {
            "rainfall_points": None,
            "historical_exposure_points": 0.0,
            "citizen_report_points": 0.0,
            "maximum_total_points": int(config.maximum_total_points),
        },
    }

    if not rainfall_input:
        base["reasons"].append("A complete usable weather input is unavailable; a current risk score was not calculated.")
        return base

    rainfall_status, rainfall_reason, window_start, window_end = _rainfall_validation(rainfall_input, now, config)
    base["data_status"]["rainfall"] = rainfall_status
    if rainfall_reason:
        base["reasons"].append(rainfall_reason)
        return base

    value = rainfall_input.get("value")
    kind = rainfall_input.get("kind")
    period_minutes = rainfall_input.get("period_minutes")
    rainfall_points = min(config.max_rainfall_points, (float(value) / config.rainfall_normalization_mm) * config.max_rainfall_points)

    exposure_pct: float | None = None
    if isinstance(ward, dict):
        raw_exposure = ward.get("percentage_of_ward_population_potentially_exposed_percent")
        if _valid_amount(raw_exposure):
            exposure_pct = max(0.0, min(100.0, float(raw_exposure)))
    exposure_points = (exposure_pct / 100.0) * config.max_exposure_points if exposure_pct is not None else 0.0

    report_points, reports_simulated, report_group_count = _report_points(
        report_list, ward_code=ward_code, now=now, config=config
    )
    score = max(0, min(config.maximum_total_points, int(round(rainfall_points + exposure_points + report_points))))

    rain_label = "Forecast" if kind == "forecast" else "Observed"
    reasons = [f"{rain_label} precipitation input: {float(value):g} mm over {period_minutes} minutes."]
    if kind == "forecast" and window_start and window_end:
        reasons.append(
            f"Forecast window: {_iso_utc(window_start)} to {_iso_utc(window_end)} (end exclusive)."
        )
    if exposure_pct is not None:
        reasons.append(
            f"Historical exposure contributes context ({exposure_pct:g}% of ward population in the source assessment; underlying population data year 2011)."
        )
    else:
        reasons.append("No usable historical exposure percentage was supplied; the exposure contribution is zero.")
    if report_points > 0:
        reasons.append(
            f"Eligible incident reports contribute up to {config.max_report_points:g} points after {config.report_eligibility_minutes}-minute decay and duplicate-candidate grouping ({report_group_count} scoring groups). Reports are not automatically confirmed incidents."
        )
    if kind == "forecast":
        reasons.append("This is a forecast-based prototype index, not confirmation of flooding or a calibrated flood probability.")
    if rainfall_is_simulated:
        reasons.append("Weather input is simulated; this assessment is not a live weather assessment or real warning.")
    if reports_simulated:
        reasons.append("One or more contributing or supplied incident reports are simulated; this assessment is labelled simulated.")

    base.update(
        {
            "risk_score": score,
            "risk_level": _level(score, config),
            "reasons": reasons,
            "score_components": {
                "rainfall_points": round(rainfall_points, 3),
                "historical_exposure_points": round(exposure_points, 3),
                "citizen_report_points": round(report_points, 3),
                "maximum_total_points": int(config.maximum_total_points),
            },
        }
    )
    base["is_simulated"] = any_simulated
    if rainfall_status == "simulated":
        base["data_status"]["rainfall"] = "simulated"
    return base
