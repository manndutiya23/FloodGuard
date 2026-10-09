"""Validate Mumbai ward-boundary GeoJSON against FloodGuard's ward reference CSV.

Run from the repository root:
    python backend/validate_ward_boundaries.py

The validator checks GeoJSON structure, polygon coordinate sanity, ward-code
coverage, duplicate/missing/extra codes, and conflicts between common code
properties. It does not prove the source geometry's legal authority, vintage,
spatial topology, or accuracy; those still require source review and visual QA.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEOJSON_PATH = REPOSITORY_ROOT / "data" / "reference" / "mumbai_ward_boundaries.geojson"
DEFAULT_CSV_PATH = REPOSITORY_ROOT / "data" / "reference" / "floodguard_mumbai_ward_flood_exposure.csv"
SUPPORTED_GEOMETRIES = {"Polygon", "MultiPolygon"}
CODE_PROPERTY_CANDIDATES = ("NAME2", "Name", "NAME", "ward_code", "WARD_CODE", "Ward_Code")


def normalize_code(value: object) -> str | None:
    """Normalize casing and embedded/newline whitespace from ward code values."""
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split()).upper()
    return normalized or None


def read_expected_ward_codes(csv_path: str | Path = DEFAULT_CSV_PATH) -> list[str]:
    """Read and validate ward_code identifiers from FloodGuard's reference CSV."""
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "ward_code" not in reader.fieldnames:
            raise ValueError("Reference CSV must contain a 'ward_code' column.")
        codes: list[str] = []
        for line_number, row in enumerate(reader, start=2):
            code = normalize_code(row.get("ward_code"))
            if code is None:
                raise ValueError(f"Reference CSV row {line_number} has a blank ward_code.")
            codes.append(code)
    if len(codes) != len(set(codes)):
        raise ValueError("Reference CSV has duplicate ward_code values after normalization.")
    if not codes:
        raise ValueError("Reference CSV contains no ward codes.")
    return codes


def _validate_position(position: object, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(position, list) or len(position) < 2:
        return [f"{context}: coordinate position must be an array with longitude and latitude."]
    lon, lat = position[0], position[1]
    for name, value in (("longitude", lon), ("latitude", lat)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"{context}: {name} must be a finite number.")
    if errors:
        return errors
    if not -180 <= lon <= 180:
        errors.append(f"{context}: longitude {lon!r} is outside [-180, 180].")
    if not -90 <= lat <= 90:
        errors.append(f"{context}: latitude {lat!r} is outside [-90, 90].")
    return errors


def _validate_ring(ring: object, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(ring, list) or len(ring) < 4:
        return [f"{context}: linear ring must contain at least four positions."]
    for index, position in enumerate(ring):
        errors.extend(_validate_position(position, f"{context} position {index}"))
    if isinstance(ring[0], list) and isinstance(ring[-1], list):
        if len(ring[0]) >= 2 and len(ring[-1]) >= 2 and ring[0][:2] != ring[-1][:2]:
            errors.append(f"{context}: linear ring is not closed (first and last positions differ).")
    return errors


def _validate_polygon_coordinates(coordinates: object, context: str) -> list[str]:
    if not isinstance(coordinates, list) or not coordinates:
        return [f"{context}: polygon coordinates must contain at least one linear ring."]
    errors: list[str] = []
    for ring_index, ring in enumerate(coordinates):
        errors.extend(_validate_ring(ring, f"{context} ring {ring_index}"))
    return errors


def _validate_geometry(geometry: object, context: str) -> list[str]:
    if not isinstance(geometry, dict):
        return [f"{context}: missing or invalid geometry object."]
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type not in SUPPORTED_GEOMETRIES:
        return [f"{context}: unsupported geometry type {geometry_type!r}; expected Polygon or MultiPolygon."]
    if geometry_type == "Polygon":
        return _validate_polygon_coordinates(coordinates, context)
    if not isinstance(coordinates, list) or not coordinates:
        return [f"{context}: MultiPolygon coordinates must contain at least one polygon."]
    errors: list[str] = []
    for polygon_index, polygon_coordinates in enumerate(coordinates):
        errors.extend(_validate_polygon_coordinates(polygon_coordinates, f"{context} polygon {polygon_index}"))
    return errors


def _resolve_feature_code(properties: object, expected_codes: set[str], context: str) -> tuple[str | None, list[str]]:
    if not isinstance(properties, dict):
        return None, [f"{context}: properties must be an object."]
    matches: list[tuple[str, str]] = []
    for property_name in CODE_PROPERTY_CANDIDATES:
        if property_name not in properties:
            continue
        code = normalize_code(properties.get(property_name))
        if code in expected_codes:
            matches.append((property_name, code))

    unique_codes = {code for _, code in matches}
    if not unique_codes:
        observed = {key: properties.get(key) for key in CODE_PROPERTY_CANDIDATES if key in properties}
        return None, [f"{context}: no ward-code property matched the reference CSV; candidate properties={observed!r}."]
    if len(unique_codes) > 1:
        return None, [f"{context}: candidate properties disagree on ward code: {matches!r}."]
    # Prefer NAME2, which is the code-like property shown in the inspected file.
    return next(code for name, code in matches if name == "NAME2") if any(name == "NAME2" for name, _ in matches) else matches[0][1], []


def validate_geojson(payload: object, expected_ward_codes: Iterable[str]) -> list[str]:
    """Return validation errors for a GeoJSON FeatureCollection and expected ward IDs."""
    expected_list = [normalize_code(code) for code in expected_ward_codes]
    expected = {code for code in expected_list if code is not None}
    errors: list[str] = []
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        return ["GeoJSON root must be a FeatureCollection object."]
    features = payload.get("features")
    if not isinstance(features, list):
        return ["GeoJSON FeatureCollection must contain a 'features' array."]
    if len(features) != len(expected):
        errors.append(f"Feature count mismatch: GeoJSON has {len(features)} features; reference CSV has {len(expected)} unique ward codes.")

    found_codes: list[str] = []
    for index, feature in enumerate(features):
        context = f"Feature {index}"
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            errors.append(f"{context}: item must be a GeoJSON Feature object.")
            continue
        code, code_errors = _resolve_feature_code(feature.get("properties"), expected, context)
        errors.extend(code_errors)
        if code:
            found_codes.append(code)
        errors.extend(_validate_geometry(feature.get("geometry"), context))

    duplicates = sorted({code for code in found_codes if found_codes.count(code) > 1})
    missing = sorted(expected - set(found_codes))
    extra = sorted(set(found_codes) - expected)
    if duplicates:
        errors.append(f"Duplicate ward codes in GeoJSON: {', '.join(duplicates)}.")
    if missing:
        errors.append(f"Missing ward codes from GeoJSON: {', '.join(missing)}.")
    if extra:
        errors.append(f"Unexpected ward codes in GeoJSON: {', '.join(extra)}.")
    return errors


def validate_files(
    geojson_path: str | Path = DEFAULT_GEOJSON_PATH,
    csv_path: str | Path = DEFAULT_CSV_PATH,
) -> list[str]:
    """Load the source files and validate boundary features against CSV ward codes."""
    try:
        expected_codes = read_expected_ward_codes(csv_path)
    except (OSError, csv.Error, ValueError) as exc:
        return [f"Could not read expected ward codes: {exc}"]
    try:
        with Path(geojson_path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Could not read GeoJSON at {geojson_path}: {exc}"]
    return validate_geojson(payload, expected_codes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geojson", default=str(DEFAULT_GEOJSON_PATH), help="Path to Mumbai ward GeoJSON")
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH), help="Path to FloodGuard ward exposure CSV")
    args = parser.parse_args()
    errors = validate_files(args.geojson, args.csv)
    if errors:
        print("FAIL: ward-boundary validation found issues:")
        for error in errors:
            print(f"- {error}")
        print("\nNote: structural checks do not prove the source's legal authority, boundary vintage, or spatial topology.")
        return 1
    print("PASS: GeoJSON contains one structurally valid polygon feature for every reference ward code.")
    print("Reminder: confirm source attribution/licence and visually inspect the boundaries before integration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
