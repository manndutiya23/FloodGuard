"""Contract-first tests for the FloodGuard risk-scoring rules.

These tests describe the target contract agreed in docs/API_CONTRACT.md.
Some tests will fail against the older implementation until the weather adapter,
forecast aggregation, and risk engine are updated to the new timestamp schema.

Provisional report behavior in this test file is intentionally qualitative:
- two-hour eligibility window;
- gradual age decay;
- verified reports have more influence than unverified reports;
- caller-supplied duplicate_group_id identifies likely duplicate groups;
- total report contribution is capped at ten points.
Numeric rainfall normalization and duplicate proximity/time detection thresholds
are provisional constants documented in docs/RISK_SCORING_DECISIONS.md.
"""
from datetime import datetime, timezone

import pytest

import app as app_module
import risk_engine
from risk_engine import RiskScoringConfig, assess_risk


NOW = "2026-10-09T10:00:00Z"
NOW_DT = datetime.fromisoformat(NOW.replace("Z", "+00:00"))
WARD = {
    "ward_code": "F/N",
    "percentage_of_ward_population_potentially_exposed_percent": 66.8,
    "underlying_population_data_year": 2011,
}

# A derived, complete three-hour forecast accumulation. The window start is
# exactly the evaluation time; the end is exclusive and three hours later.
RAINFALL = {
    "kind": "forecast",
    "value": 12.0,
    "unit": "mm",
    "period_minutes": 180,
    "forecast_window_start": "2026-10-09T10:00:00Z",
    "forecast_window_end": "2026-10-09T13:00:00Z",
    "retrieved_at": "2026-10-09T09:59:00Z",
    "source": "Open-Meteo",
    "status": "available",
    "is_simulated": False,
}


def _report(
    report_id="report-1",
    *,
    minutes_old=0,
    verification_status="unverified",
    is_simulated=False,
    duplicate_group_id=None,
    **extra,
):
    reported_at = (NOW_DT.timestamp() - minutes_old * 60)
    timestamp = datetime.fromtimestamp(reported_at, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    result = {
        "report_id": report_id,
        "reported_at": timestamp,
        "status": "new",
        "verification_status": verification_status,
        "is_simulated": is_simulated,
        "ward_code": "F/N",
        "category": "waterlogging",
    }
    if duplicate_group_id is not None:
        result["duplicate_group_id"] = duplicate_group_id
    result.update(extra)
    return result


def _score(*, rainfall=RAINFALL, reports=None, ward=WARD, evaluated_at=NOW, config=None):
    return assess_risk(
        ward=ward,
        rainfall=rainfall,
        reports=reports,
        evaluated_at=evaluated_at,
        config=config,
    )


def test_calculates_explainable_three_hour_forecast_score():
    result = _score(reports=[])

    assert result["ward_code"] == "F/N"
    assert result["risk_score"] is not None
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in {"low", "moderate", "high"}
    assert any("Forecast precipitation" in reason for reason in result["reasons"])
    assert result["data_status"]["historical_baseline"] == "available"
    assert result["data_status"]["rainfall"] == "available"


def test_forecast_aggregation_uses_only_future_three_hour_values(monkeypatch):
    """The API forecast helper must use forecast_valid_at, not a generic timestamp."""
    monkeypatch.setattr(app_module, "_utc_now", lambda: NOW_DT)
    weather = {
        "source": "Open-Meteo",
        "status": "available",
        "is_simulated": False,
        "retrieved_at": "2026-10-09T09:59:00Z",
        "hours": [
            {"forecast_valid_at": "2026-10-09T08:00:00Z", "precipitation_mm": 100.0},
            {"forecast_valid_at": "2026-10-09T09:00:00Z", "precipitation_mm": 100.0},
            {"forecast_valid_at": "2026-10-09T10:00:00Z", "precipitation_mm": 1.0},
            {"forecast_valid_at": "2026-10-09T11:00:00Z", "precipitation_mm": 2.0},
            {"forecast_valid_at": "2026-10-09T12:00:00Z", "precipitation_mm": 3.0},
            {"forecast_valid_at": "2026-10-09T13:00:00Z", "precipitation_mm": 4.0},
        ],
    }

    signal = app_module._forecast_signal(weather)

    assert signal is not None
    assert signal["value"] == 6.0
    assert signal["period_minutes"] == 180
    assert signal["forecast_window_start"] == "2026-10-09T10:00:00Z"
    assert signal["forecast_window_end"] == "2026-10-09T13:00:00Z"
    assert signal["retrieved_at"] == "2026-10-09T09:59:00Z"
    assert "observed_at" not in signal


def test_incomplete_three_hour_forecast_window_is_not_aggregated(monkeypatch):
    """A missing value inside the required window must not be skipped or zero-filled."""
    monkeypatch.setattr(app_module, "_utc_now", lambda: NOW_DT)
    weather = {
        "source": "Open-Meteo",
        "status": "available",
        "is_simulated": False,
        "retrieved_at": "2026-10-09T09:59:00Z",
        "hours": [
            {"forecast_valid_at": "2026-10-09T10:00:00Z", "precipitation_mm": 1.0},
            {"forecast_valid_at": "2026-10-09T11:00:00Z", "precipitation_mm": None},
            {"forecast_valid_at": "2026-10-09T12:00:00Z", "precipitation_mm": 3.0},
            {"forecast_valid_at": "2026-10-09T13:00:00Z", "precipitation_mm": 4.0},
        ],
    }

    assert app_module._forecast_signal(weather) is None


def test_missing_or_incomplete_forecast_returns_unknown_not_low():
    incomplete = {
        **RAINFALL,
        "value": None,
        "status": "unavailable",
        "error_code": "INCOMPLETE_FORECAST_WINDOW",
    }
    result = _score(rainfall=incomplete, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_missing_rainfall_returns_unknown_not_low():
    result = _score(rainfall=None, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_historical_exposure_alone_cannot_create_score():
    result = _score(rainfall=None, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"


def test_observation_older_than_180_minutes_is_stale():
    rainfall = {
        "kind": "observation",
        "value": 4.0,
        "unit": "mm",
        "period_minutes": 60,
        "observed_at": "2026-10-09T06:59:00Z",  # 181 minutes before NOW
        "retrieved_at": "2026-10-09T09:59:00Z",
        "source": "test-observation-provider",
        "status": "available",
        "is_simulated": False,
    }
    result = _score(rainfall=rainfall, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "stale"


def test_observation_at_180_minute_boundary_is_not_stale():
    rainfall = {
        "kind": "observation",
        "value": 4.0,
        "unit": "mm",
        "period_minutes": 60,
        "observed_at": "2026-10-09T07:00:00Z",  # exactly 180 minutes old
        "retrieved_at": "2026-10-09T09:59:00Z",
        "source": "test-observation-provider",
        "status": "available",
        "is_simulated": False,
    }
    result = _score(rainfall=rainfall, reports=[])

    assert result["risk_score"] is not None
    assert result["data_status"]["rainfall"] == "available"


def test_future_observation_timestamp_is_rejected():
    rainfall = {
        "kind": "observation",
        "value": 4.0,
        "unit": "mm",
        "period_minutes": 60,
        "observed_at": "2026-10-09T10:01:00Z",
        "retrieved_at": "2026-10-09T09:59:00Z",
        "source": "test-observation-provider",
        "status": "available",
        "is_simulated": False,
    }
    result = _score(rainfall=rainfall, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_fully_elapsed_forecast_window_is_not_scored():
    rainfall = {
        **RAINFALL,
        "forecast_window_start": "2026-10-09T06:00:00Z",
        "forecast_window_end": "2026-10-09T09:00:00Z",
    }
    result = _score(rainfall=rainfall, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "stale"


def test_forecast_window_overlapping_elapsed_time_is_rejected():
    rainfall = {
        **RAINFALL,
        "forecast_window_start": "2026-10-09T09:00:00Z",
        "forecast_window_end": "2026-10-09T12:00:00Z",
    }
    result = _score(rainfall=rainfall, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_forecast_window_must_be_exactly_three_hours():
    rainfall = {
        **RAINFALL,
        "period_minutes": 360,
        "forecast_window_end": "2026-10-09T16:00:00Z",
    }
    result = _score(rainfall=rainfall, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_invalid_rainfall_unit_returns_unknown():
    result = _score(rainfall={**RAINFALL, "unit": "inch"}, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_rainfall_returns_unknown(value):
    result = _score(rainfall={**RAINFALL, "value": value}, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_negative_rainfall_returns_unknown():
    result = _score(rainfall={**RAINFALL, "value": -0.1}, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_malformed_observation_timestamp_returns_unknown():
    rainfall = {
        "kind": "observation",
        "value": 4.0,
        "unit": "mm",
        "period_minutes": 60,
        "observed_at": "not-a-timestamp",
        "retrieved_at": "2026-10-09T09:59:00Z",
        "source": "test-observation-provider",
        "status": "available",
        "is_simulated": False,
    }
    result = _score(rainfall=rainfall, reports=[])

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_simulated_weather_marks_result_simulated():
    result = _score(rainfall={**RAINFALL, "is_simulated": True}, reports=[])

    assert result["risk_score"] is not None
    assert result["is_simulated"] is True
    assert result["data_status"]["rainfall"] == "simulated"


def test_simulated_status_can_be_scored_and_labelled_simulated():
    result = _score(
        rainfall={**RAINFALL, "status": "simulated", "is_simulated": True},
        reports=[],
    )

    assert result["risk_score"] is not None
    assert result["risk_level"] in {"low", "moderate", "high"}
    assert result["is_simulated"] is True
    assert result["data_status"]["rainfall"] == "simulated"


def test_simulated_report_marks_result_simulated():
    result = _score(
        reports=[_report(is_simulated=True, verification_status="unverified")]
    )

    assert result["is_simulated"] is True


def test_recent_verified_report_contributes_more_than_unverified_report():
    baseline = _score(reports=[])["risk_score"]
    unverified = _score(
        reports=[_report("unverified", minutes_old=30, verification_status="unverified")]
    )["risk_score"]
    verified = _score(
        reports=[_report("verified", minutes_old=30, verification_status="verified")]
    )["risk_score"]

    assert unverified > baseline
    assert verified > unverified


def test_report_contribution_decays_gradually_with_age():
    scores = [
        _score(reports=[_report(f"verified-{age}", minutes_old=age,
                                verification_status="verified")])["risk_score"]
        for age in (0, 30, 60, 90)
    ]

    assert scores[0] > scores[1] > scores[2] > scores[3]


def test_report_at_or_older_than_two_hour_window_does_not_contribute():
    baseline = _score(reports=[])["risk_score"]
    exactly_two_hours = _score(
        reports=[_report("report-120", minutes_old=120, verification_status="verified")]
    )["risk_score"]
    too_old = _score(
        reports=[_report("report-121", minutes_old=121, verification_status="verified")]
    )["risk_score"]

    assert exactly_two_hours == baseline
    assert too_old == baseline


def test_future_report_does_not_contribute():
    baseline = _score(reports=[])["risk_score"]
    future_time = datetime.fromtimestamp(
        NOW_DT.timestamp() + 60, tz=timezone.utc
    ).isoformat().replace("+00:00", "Z")
    future_report = {
        **_report("future-report"),
        "reported_at": future_time,
        "verification_status": "verified",
    }
    result = _score(reports=[future_report])

    assert result["risk_score"] == baseline


def test_reports_in_same_duplicate_group_are_not_double_counted():
    single = _score(
        reports=[
            _report("report-a", minutes_old=15, verification_status="verified",
                    duplicate_group_id="nearby-waterlogging-1")
        ]
    )["risk_score"]
    duplicates = _score(
        reports=[
            _report("report-a", minutes_old=15, verification_status="verified",
                    duplicate_group_id="nearby-waterlogging-1"),
            _report("report-b", minutes_old=16, verification_status="verified",
                    duplicate_group_id="nearby-waterlogging-1"),
        ]
    )["risk_score"]

    assert duplicates == single


def test_independent_report_groups_can_reinforce_but_contribution_is_capped():
    baseline = _score(reports=[])["risk_score"]
    a_few = _score(
        reports=[
            _report("independent-1", verification_status="verified", duplicate_group_id="g1"),
            _report("independent-2", verification_status="verified", duplicate_group_id="g2"),
        ]
    )["risk_score"]
    many = _score(
        reports=[
            _report(
                f"independent-{index}",
                verification_status="verified",
                duplicate_group_id=f"g{index}",
            )
            for index in range(1, 25)
        ]
    )["risk_score"]

    assert a_few > baseline
    assert many >= a_few
    assert many <= baseline + 10
    assert many <= 100


def test_total_score_is_capped_at_100():
    maximum_ward = {
        **WARD,
        "percentage_of_ward_population_potentially_exposed_percent": 100.0,
    }
    high_rainfall = {**RAINFALL, "value": 1000.0}
    reports = [
        _report(f"high-{i}", verification_status="verified", duplicate_group_id=f"g{i}")
        for i in range(1, 25)
    ]
    result = _score(ward=maximum_ward, rainfall=high_rainfall, reports=reports)

    assert result["risk_score"] == 100
    assert result["risk_level"] == "high"


def test_score_and_level_thresholds_remain_explicitly_provisional():
    assert risk_engine._level(29) == "low"
    assert risk_engine._level(30) == "moderate"
    assert risk_engine._level(59) == "moderate"
    assert risk_engine._level(60) == "high"


def test_thirty_mm_over_three_hours_reaches_full_rainfall_allocation():
    rainfall = {**RAINFALL, "value": 30.0}
    ward_without_exposure = {**WARD, "percentage_of_ward_population_potentially_exposed_percent": 0.0}
    result = _score(rainfall=rainfall, ward=ward_without_exposure, reports=[])

    assert result["score_components"]["rainfall_points"] == 70.0
    assert result["score_components"]["historical_exposure_points"] == 0.0
    assert result["score_components"]["citizen_report_points"] == 0.0


def test_rainfall_contribution_is_capped_above_thirty_mm():
    ward_without_exposure = {**WARD, "percentage_of_ward_population_potentially_exposed_percent": 0.0}
    result = _score(
        rainfall={**RAINFALL, "value": 90.0},
        ward=ward_without_exposure,
        reports=[],
    )

    assert result["score_components"]["rainfall_points"] == 70.0
    assert result["risk_score"] == 70


def test_report_base_weights_and_linear_decay_are_explicit():
    verified_now = _score(reports=[_report("v0", minutes_old=0, verification_status="verified")])
    unverified_now = _score(reports=[_report("u0", minutes_old=0, verification_status="unverified")])
    verified_60 = _score(reports=[_report("v60", minutes_old=60, verification_status="verified")])
    verified_90 = _score(reports=[_report("v90", minutes_old=90, verification_status="verified")])
    verified_120 = _score(reports=[_report("v120", minutes_old=120, verification_status="verified")])

    assert verified_now["score_components"]["citizen_report_points"] == 6.0
    assert unverified_now["score_components"]["citizen_report_points"] == 2.0
    assert verified_60["score_components"]["citizen_report_points"] == 3.0
    assert verified_90["score_components"]["citizen_report_points"] == 1.5
    assert verified_120["score_components"]["citizen_report_points"] == 0.0


def test_spatially_and_temporally_close_reports_are_grouped_as_candidates():
    first = _report("near-a", minutes_old=15, verification_status="verified", latitude=19.0760, longitude=72.8777)
    second = _report("near-b", minutes_old=10, verification_status="verified", latitude=19.0765, longitude=72.8777)
    single_first = _score(reports=[first])
    single_second = _score(reports=[second])
    source_reports = [first.copy(), second.copy()]
    grouped = _score(reports=source_reports)

    # A candidate group contributes only its strongest single report, not the sum.
    assert grouped["score_components"]["citizen_report_points"] == max(
        single_first["score_components"]["citizen_report_points"],
        single_second["score_components"]["citizen_report_points"],
    )
    assert len(source_reports) == 2  # source records are preserved, not removed
    assert any("duplicate-candidate grouping" in reason for reason in grouped["reasons"])


def test_report_outside_duplicate_distance_can_reinforce_signal():
    first = _report("near-a", minutes_old=15, verification_status="verified", latitude=19.0760, longitude=72.8777)
    distant = _report("far-b", minutes_old=10, verification_status="verified", latitude=19.0790, longitude=72.8777)
    single = _score(reports=[first])
    independent = _score(reports=[first, distant])

    assert independent["score_components"]["citizen_report_points"] > single["score_components"]["citizen_report_points"]


def test_report_outside_duplicate_time_window_can_reinforce_signal():
    first = _report("near-a", minutes_old=40, verification_status="verified", latitude=19.0760, longitude=72.8777)
    later = _report("near-b", minutes_old=5, verification_status="verified", latitude=19.0761, longitude=72.8777)
    single = _score(reports=[first])
    independent = _score(reports=[first, later])

    assert independent["score_components"]["citizen_report_points"] > single["score_components"]["citizen_report_points"]



def test_duplicate_detection_thresholds_are_configurable():
    first = _report("config-a", minutes_old=15, verification_status="verified", latitude=19.0760, longitude=72.8777)
    second = _report("config-b", minutes_old=10, verification_status="verified", latitude=19.0765, longitude=72.8777)
    default_result = _score(reports=[first, second])
    strict_config = RiskScoringConfig(report_duplicate_distance_meters=20.0)
    stricter_result = _score(reports=[first, second], config=strict_config)

    assert stricter_result["score_components"]["citizen_report_points"] > default_result["score_components"]["citizen_report_points"]



def test_reports_without_ward_match_do_not_affect_ward_score():
    baseline = _score(reports=[])
    unmatched = _report("unmatched", minutes_old=5, verification_status="verified")
    unmatched.pop("ward_code")
    result = _score(reports=[unmatched])

    assert result["risk_score"] == baseline["risk_score"]


def test_resolved_reports_do_not_contribute_to_current_signal():
    baseline = _score(reports=[])
    resolved = _report("resolved", minutes_old=5, verification_status="verified", status="resolved")
    result = _score(reports=[resolved])

    assert result["risk_score"] == baseline["risk_score"]
