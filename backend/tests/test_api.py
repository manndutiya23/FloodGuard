from datetime import datetime, timezone

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
    assert result["latest_available_info"] is None


def test_risk_endpoint_keeps_latest_context_separate_if_window_incomplete(monkeypatch):
    now = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(app_module, "_utc_now", lambda: now)
    monkeypatch.setattr(
        app_module,
        "fetch_hourly_precipitation",
        lambda latitude, longitude: {
            "source": "Open-Meteo",
            "source_type": "weather_model_forecast",
            "status": "available",
            "is_simulated": False,
            "retrieved_at": "2026-10-09T09:59:00Z",
            "hours": [
                {"forecast_valid_at": "2026-10-09T09:00:00Z", "precipitation_mm": 8.2},
                {"forecast_valid_at": "2026-10-09T10:00:00Z", "precipitation_mm": 1.0},
                {"forecast_valid_at": "2026-10-09T11:00:00Z", "precipitation_mm": None},
                {"forecast_valid_at": "2026-10-09T12:00:00Z", "precipitation_mm": 3.0},
                {"forecast_valid_at": "2026-10-09T13:00:00Z", "precipitation_mm": 4.0},
            ],
        },
    )

    response = client.get("/risk?ward_code=F%2FN")
    assert response.status_code == 200
    result = response.json()["data"][0]
    assert result["risk_score"] is None
    assert result["risk_level"] == "unknown"
    assert result["latest_available_info"]["precipitation_mm"] == 1.0
    assert result["latest_available_info"]["forecast_valid_at"] == "2026-10-09T10:00:00Z"
    assert result["latest_available_info"]["retrieved_at"] == "2026-10-09T09:59:00Z"
    assert result["latest_available_info"]["retrieval_age_minutes"] == 1
    assert any("complete three-hour future forecast window" in reason for reason in result["reasons"])



def test_create_report_persists_server_controlled_fields(monkeypatch):
    saved = {}

    class FakeTable:
        def put_item(self, **kwargs):
            saved.update(kwargs["Item"])

    monkeypatch.setenv("REPORTS_TABLE_NAME", "floodguard-reports")
    monkeypatch.setattr(app_module, "_reports_table", lambda: FakeTable())

    response = client.post(
        "/reports",
        json={
            "latitude": 19.076,
            "longitude": 72.8777,
            "category": "waterlogging",
            "description": "Water near Gate 2",
            "status": "resolved",
            "verification_status": "verified",
            "ward_code": "F/N",
            "is_simulated": True,
        },
    )

    assert response.status_code == 201
    report = response.json()["data"]
    assert report["status"] == "new"
    assert report["verification_status"] == "unverified"
    assert report["is_simulated"] is False
    assert report["ward_code"] is None
    assert saved["report_id"] == report["report_id"]


def test_create_report_rejects_invalid_category():
    response = client.post(
        "/reports",
        json={"latitude": 19.076, "longitude": 72.8777, "category": "fire"},
    )
    assert response.status_code == 422


def test_list_reports_filters_and_sorts(monkeypatch):
    class FakeTable:
        def scan(self):
            return {"Items": [
                {"report_id": "old", "status": "new", "ward_code": "A", "reported_at": "2026-10-09T09:00:00Z"},
                {"report_id": "new", "status": "new", "ward_code": "A", "reported_at": "2026-10-09T10:00:00Z"},
                {"report_id": "resolved", "status": "resolved", "ward_code": "A", "reported_at": "2026-10-09T11:00:00Z"},
            ]}

    monkeypatch.setenv("REPORTS_TABLE_NAME", "floodguard-reports")
    monkeypatch.setattr(app_module, "_reports_table", lambda: FakeTable())
    response = client.get("/reports?status=new&ward_code=A&limit=1")
    assert response.status_code == 200
    assert [item["report_id"] for item in response.json()["data"]] == ["new"]
