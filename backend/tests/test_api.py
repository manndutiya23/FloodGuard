import pytest
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
    # The ward comes from boundary geometry, not from the client-supplied "F/N".
    assert report["ward_code"] == "L"
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


def test_create_report_leaves_ward_null_outside_boundaries(monkeypatch):
    class FakeTable:
        def put_item(self, **kwargs):
            pass

    monkeypatch.setenv("REPORTS_TABLE_NAME", "floodguard-reports")
    monkeypatch.setattr(app_module, "_reports_table", lambda: FakeTable())
    response = client.post("/reports", json={"latitude": 19.05, "longitude": 72.70, "category": "waterlogging"})
    assert response.status_code == 201
    assert response.json()["data"]["ward_code"] is None


def test_create_report_still_saves_if_ward_lookup_fails(monkeypatch):
    class FakeTable:
        def put_item(self, **kwargs):
            pass

    def broken_lookup(latitude, longitude):
        raise OSError("boundary file missing")

    monkeypatch.setenv("REPORTS_TABLE_NAME", "floodguard-reports")
    monkeypatch.setattr(app_module, "_reports_table", lambda: FakeTable())
    monkeypatch.setattr(app_module, "find_ward", broken_lookup)
    response = client.post("/reports", json={"latitude": 19.076, "longitude": 72.8777, "category": "waterlogging"})
    assert response.status_code == 201
    assert response.json()["data"]["ward_code"] is None


class ConditionalCheckFailed(Exception):
    response = {"Error": {"Code": "ConditionalCheckFailedException"}}


def test_update_report_status_changes_only_workflow_status(monkeypatch):
    calls = {}

    class FakeTable:
        def update_item(self, **kwargs):
            calls.update(kwargs)
            return {"Attributes": {
                "report_id": "abc",
                "status": kwargs["ExpressionAttributeValues"][":status"],
                "verification_status": "unverified",
            }}

    monkeypatch.setenv("REPORTS_TABLE_NAME", "floodguard-reports")
    monkeypatch.setattr(app_module, "_reports_table", lambda: FakeTable())
    response = client.patch("/reports/abc", json={"status": "reviewed", "verification_status": "verified"})

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "reviewed"
    assert response.json()["data"]["verification_status"] == "unverified"
    assert calls["Key"] == {"report_id": "abc"}
    assert calls["ConditionExpression"] == "attribute_exists(report_id)"
    assert "verification_status" not in calls["UpdateExpression"]


def test_update_report_status_returns_404_for_unknown_report(monkeypatch):
    class FakeTable:
        def update_item(self, **kwargs):
            raise ConditionalCheckFailed()

    monkeypatch.setenv("REPORTS_TABLE_NAME", "floodguard-reports")
    monkeypatch.setattr(app_module, "_reports_table", lambda: FakeTable())
    response = client.patch("/reports/missing", json={"status": "resolved"})
    assert response.status_code == 404


def test_update_report_status_rejects_upload_records_and_invalid_status(monkeypatch):
    monkeypatch.setattr(app_module, "_reports_table", lambda: pytest.fail("must not reach the table"))
    assert client.patch("/reports/UPLOAD%23abc", json={"status": "reviewed"}).status_code == 404
    assert client.patch("/reports/abc", json={"status": "verified"}).status_code == 422


def test_update_report_status_returns_503_on_storage_error(monkeypatch):
    class FakeTable:
        def update_item(self, **kwargs):
            raise RuntimeError("throttled")

    monkeypatch.setenv("REPORTS_TABLE_NAME", "floodguard-reports")
    monkeypatch.setattr(app_module, "_reports_table", lambda: FakeTable())
    assert client.patch("/reports/abc", json={"status": "reviewed"}).status_code == 503
