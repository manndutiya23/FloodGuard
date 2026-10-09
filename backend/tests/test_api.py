from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "floodguard-api"}


def test_wards_endpoint_returns_reference_rows():
    response = client.get("/wards")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 24
    assert payload["data"][0]["ward_code"] == "A"
    assert payload["meta"]["data_type"] == "historical_vulnerability_baseline"


def test_weather_endpoint_handles_unavailable_provider(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "fetch_hourly_precipitation",
        lambda latitude, longitude: {
            "source": "Open-Meteo",
            "source_type": "weather_model_forecast",
            "status": "unavailable",
            "is_simulated": False,
            "retrieved_at": "2026-10-09T10:00:00Z",
            "hours": [],
            "error_code": "WEATHER_REQUEST_ERROR",
        },
    )
    response = client.get("/weather")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "unavailable"


def test_risk_endpoint_returns_unknown_when_weather_unavailable(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "fetch_hourly_precipitation",
        lambda latitude, longitude: {
            "source": "Open-Meteo",
            "source_type": "weather_model_forecast",
            "status": "unavailable",
            "is_simulated": False,
            "retrieved_at": "2026-10-09T10:00:00Z",
            "hours": [],
            "error_code": "WEATHER_REQUEST_ERROR",
        },
    )
    response = client.get("/risk?ward_code=F%2FN")
    assert response.status_code == 200
    result = response.json()["data"][0]
    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
