import pytest

from validate_ward_boundaries import normalize_code, validate_geojson


def square_geometry():
    # Tiny valid polygon around a generic coordinate; topology isn't the focus here.
    return {
        "type": "Polygon",
        "coordinates": [[
            [72.0, 19.0], [72.1, 19.0], [72.1, 19.1], [72.0, 19.1], [72.0, 19.0]
        ]],
    }


def feature(code, *, secondary_code=None, geometry=None):
    return {
        "type": "Feature",
        "properties": {"Name": f" {code} ", "NAME2": f"{secondary_code or code}\n"},
        "geometry": geometry or square_geometry(),
    }


def collection(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def test_normalize_code_removes_newlines_and_extra_whitespace():
    assert normalize_code("\n   G/S  \n") == "G/S"


def test_matching_two_feature_collection_passes():
    assert validate_geojson(collection(feature("A"), feature("F/N")), ["A", "F/N"]) == []


def test_missing_ward_is_reported():
    errors = validate_geojson(collection(feature("A")), ["A", "F/N"])
    assert any("Feature count mismatch" in error for error in errors)
    assert any("Missing ward codes" in error and "F/N" in error for error in errors)


def test_duplicate_ward_is_reported():
    errors = validate_geojson(collection(feature("A"), feature("A")), ["A", "F/N"])
    assert any("Duplicate ward codes" in error and "A" in error for error in errors)


def test_conflicting_code_properties_are_reported():
    errors = validate_geojson(collection(feature("A", secondary_code="F/N")), ["A", "F/N"])
    assert any("properties disagree" in error for error in errors)


def test_missing_or_invalid_geometry_is_reported():
    errors = validate_geojson(collection(feature("A", geometry=None), feature("F/N", geometry={"type": "Point", "coordinates": [72, 19]})), ["A", "F/N"])
    assert any("unsupported geometry type" in error for error in errors)


def test_open_polygon_ring_is_rejected():
    bad = {"type": "Polygon", "coordinates": [[[72, 19], [72.1, 19], [72.1, 19.1], [72, 19.1]]]}
    errors = validate_geojson(collection(feature("A", geometry=bad)), ["A"])
    assert any("not closed" in error for error in errors)


def test_out_of_range_coordinates_are_rejected():
    bad = {"type": "Polygon", "coordinates": [[[200, 19], [201, 19], [201, 20], [200, 20], [200, 19]]]}
    errors = validate_geojson(collection(feature("A", geometry=bad)), ["A"])
    assert any("longitude" in error and "outside" in error for error in errors)


def test_multipolygon_is_supported():
    polygon_coords = square_geometry()["coordinates"]
    multipolygon = {"type": "MultiPolygon", "coordinates": [polygon_coords, polygon_coords]}
    assert validate_geojson(collection(feature("A", geometry=multipolygon)), ["A"]) == []
