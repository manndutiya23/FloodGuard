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
    result = assess_risk(ward=WARD, rainfall=RAINFALL, reports=[], evaluated_at=NOW)
    assert result["ward_code"] == "F/N"
    assert result["risk_score"] is not None
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in {"low", "moderate", "high"}
    assert any("Forecast precipitation" in reason for reason in result["reasons"])
    assert result["data_status"]["historical_baseline"] == "available"


def test_missing_rainfall_returns_unknown_not_low():
    result = assess_risk(ward=WARD, rainfall=None, reports=[], evaluated_at=NOW)
    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "unavailable"


def test_historical_exposure_alone_cannot_create_score():
    result = assess_risk(ward=WARD, rainfall=None, reports=[], evaluated_at=NOW)
    assert result["risk_score"] is None


def test_stale_observation_returns_unknown():
    rainfall = {
        **RAINFALL,
        "kind": "observation",
        "timestamp": "2026-10-09T05:00:00Z",
    }
    result = assess_risk(ward=WARD, rainfall=rainfall, reports=[], evaluated_at=NOW)
    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["data_status"]["rainfall"] == "stale"


def test_simulated_input_marks_result_simulated():
    rainfall = {**RAINFALL, "is_simulated": True}
    result = assess_risk(ward=WARD, rainfall=rainfall, reports=[], evaluated_at=NOW)
    assert result["is_simulated"] is True
    assert result["data_status"]["rainfall"] == "simulated"


def test_invalid_rainfall_unit_returns_unknown():
    rainfall = {**RAINFALL, "unit": "inch"}
    result = assess_risk(ward=WARD, rainfall=rainfall, reports=[], evaluated_at=NOW)
    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
