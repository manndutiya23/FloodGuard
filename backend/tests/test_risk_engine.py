import pytest

from risk_engine import assess_risk


NOW = "2026-10-09T10:00:00Z"
WARD = {
    "ward_code": "F/N",
    "percentage_of_ward_population_potentially_exposed_percent": 66.8,
    "underlying_population_data_year": 2011,
}
RAINFALL = {
    "kind": "forecast",
    "value": 12.0,
    "unit": "mm",
    "period_minutes": 360,
    "timestamp": "2026-10-09T11:00:00Z",
    "source": "Open-Meteo",
    "status": "available",
    "is_simulated": False,
}


def test_calculates_explainable_forecast_score():
    result = assess_risk(
        ward=WARD,
        rainfall=RAINFALL,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["ward_code"] == "F/N"
    assert result["risk_score"] is not None
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in {"low", "moderate", "high"}
    assert any("Forecast precipitation" in reason for reason in result["reasons"])
    assert result["data_status"]["historical_baseline"] == "available"


def test_missing_rainfall_returns_unknown_not_low():
    result = assess_risk(
        ward=WARD,
        rainfall=None,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_historical_exposure_alone_cannot_create_score():
    result = assess_risk(
        ward=WARD,
        rainfall=None,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"


def test_stale_observation_returns_unknown():
    rainfall = {
        **RAINFALL,
        "kind": "observation",
        "timestamp": "2026-10-09T05:00:00Z",
    }
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "stale"


def test_simulated_input_marks_result_simulated():
    rainfall = {**RAINFALL, "is_simulated": True}
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is not None
    assert result["is_simulated"] is True
    assert result["data_status"]["rainfall"] == "simulated"


def test_simulated_status_can_be_scored_and_labelled_simulated():
    rainfall = {
        **RAINFALL,
        "status": "simulated",
        "is_simulated": True,
    }
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is not None
    assert result["risk_level"] in {"low", "moderate", "high"}
    assert result["is_simulated"] is True
    assert result["data_status"]["rainfall"] == "simulated"


def test_invalid_rainfall_unit_returns_unknown():
    rainfall = {**RAINFALL, "unit": "inch"}
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_rainfall_returns_unknown(value):
    rainfall = {**RAINFALL, "value": value}
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_negative_rainfall_returns_unknown():
    rainfall = {**RAINFALL, "value": -0.1}
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"


def test_future_observation_timestamp_returns_unknown():
    rainfall = {
        **RAINFALL,
        "kind": "observation",
        "timestamp": "2026-10-09T11:00:00Z",
    }
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_malformed_rainfall_timestamp_returns_unknown():
    rainfall = {**RAINFALL, "timestamp": "not-a-timestamp"}
    result = assess_risk(
        ward=WARD,
        rainfall=rainfall,
        reports=[],
        evaluated_at=NOW,
    )

    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_recent_verified_report_contributes_more_than_unverified_report():
    baseline = assess_risk(
        ward=WARD,
        rainfall=RAINFALL,
        reports=[],
        evaluated_at=NOW,
    )
    unverified = assess_risk(
        ward=WARD,
        rainfall=RAINFALL,
        reports=[
            {
                "report_id": "report-unverified",
                "reported_at": "2026-10-09T09:00:00Z",
                "status": "new",
                "verification_status": "unverified",
                "is_simulated": False,
            }
        ],
        evaluated_at=NOW,
    )
    verified = assess_risk(
        ward=WARD,
        rainfall=RAINFALL,
        reports=[
            {
                "report_id": "report-verified",
                "reported_at": "2026-10-09T09:00:00Z",
                "status": "new",
                "verification_status": "verified",
                "is_simulated": False,
            }
        ],
        evaluated_at=NOW,
    )

    assert unverified["risk_score"] > baseline["risk_score"]
    assert verified["risk_score"] > unverified["risk_score"]
    assert any("Recent incident reports contribute" in reason for reason in verified["reasons"])


def test_old_and_future_reports_do_not_contribute():
    baseline = assess_risk(
        ward=WARD,
        rainfall=RAINFALL,
        reports=[],
        evaluated_at=NOW,
    )
    result = assess_risk(
        ward=WARD,
        rainfall=RAINFALL,
        reports=[
            {
                "report_id": "old-report",
                "reported_at": "2026-10-09T02:00:00Z",
                "status": "new",
                "verification_status": "verified",
                "is_simulated": False,
            },
            {
                "report_id": "future-report",
                "reported_at": "2026-10-09T11:00:00Z",
                "status": "new",
                "verification_status": "verified",
                "is_simulated": False,
            },
        ],
        evaluated_at=NOW,
    )

    assert result["risk_score"] == baseline["risk_score"]
