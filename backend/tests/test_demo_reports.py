import json
from datetime import datetime, timezone
from pathlib import Path

import seed_demo_reports
from seed_demo_reports import DEFAULT_FIXTURE_PATH, build_items, load_fixture, validate_fixture
from validate_ward_boundaries import normalize_code

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BOUNDARIES_PATH = REPOSITORY_ROOT / "data" / "reference" / "mumbai_ward_boundaries.geojson"


def _point_in_ring(lng, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _ward_for(lat, lng):
    # The boundary file stores positions as [lat, lng]; swap to [lng, lat] here.
    collection = json.loads(BOUNDARIES_PATH.read_text(encoding="utf-8"))
    for feature in collection["features"]:
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for rings in polygons:
            swapped = [[(p[1], p[0]) for p in ring] for ring in rings]
            if _point_in_ring(lng, lat, swapped[0]) and not any(_point_in_ring(lng, lat, h) for h in swapped[1:]):
                return normalize_code(feature["properties"].get("NAME2"))
    return None


def test_fixture_is_valid():
    assert validate_fixture(load_fixture()) == []


def test_every_fixture_ward_code_matches_its_coordinates():
    for report in load_fixture():
        if report["ward_code"] is not None:
            assert _ward_for(report["latitude"], report["longitude"]) == report["ward_code"], report["report_id"]


def test_built_items_are_always_simulated_with_relative_timestamps():
    now = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
    items = build_items(load_fixture(), now=now)
    assert items and all(item["is_simulated"] is True for item in items)
    assert all(item["report_id"].startswith("demo-") for item in items)
    first = load_fixture()[0]
    expected = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc).timestamp() - first["minutes_ago"] * 60
    assert datetime.fromisoformat(items[0]["reported_at"].replace("Z", "+00:00")).timestamp() == expected


def test_validation_rejects_non_demo_ids_and_bad_values():
    bad = [{
        "report_id": "real-123",
        "minutes_ago": -1,
        "latitude": 72.8,
        "longitude": 19.0,
        "category": "fire",
        "status": "open",
        "verification_status": "maybe",
        "description": "x" * 281,
        "ward_code": None,
    }]
    errors = validate_fixture(bad)
    assert len(errors) == 8


def test_dry_run_does_not_touch_aws(monkeypatch, capsys):
    def fail():
        raise AssertionError("dry run must not access DynamoDB")

    monkeypatch.setattr(seed_demo_reports, "_reports_table", fail)
    monkeypatch.setattr("sys.argv", ["seed_demo_reports.py", "--fixture", str(DEFAULT_FIXTURE_PATH)])
    assert seed_demo_reports.main() == 0
    assert "DRY RUN" in capsys.readouterr().out
