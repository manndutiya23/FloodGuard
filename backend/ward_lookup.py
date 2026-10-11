"""Match a coordinate to a Mumbai ward using the reference boundary GeoJSON.

The source file stores positions as [latitude, longitude] rather than GeoJSON's
[longitude, latitude]. Positions are normalized at load time; the file itself is
not modified. A point outside every ward returns None: the ward is never guessed.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES_PATH = REPOSITORY_ROOT / "data" / "reference" / "mumbai_ward_boundaries.geojson"

Ring = list[tuple[float, float]]


def normalize_code(value: object) -> str | None:
    """Strip the whitespace and line breaks the source file has around ward codes."""
    if not isinstance(value, str):
        return None
    code = "".join(value.split()).upper()
    return code or None


def _looks_lat_first(position: list[float]) -> bool:
    # Mumbai: latitude ~18.8-19.4, longitude ~72.7-73.1.
    return 18.0 <= position[0] <= 20.0 and 72.0 <= position[1] <= 74.0


def _to_lng_lat(ring: list[list[float]], swap: bool) -> Ring:
    return [(p[1], p[0]) if swap else (p[0], p[1]) for p in ring]


@lru_cache(maxsize=1)
def load_wards(path: str = str(BOUNDARIES_PATH)) -> tuple[tuple[str, tuple[tuple[Ring, ...], ...]], ...]:
    """Return (ward_code, polygons) pairs; each polygon is (outer ring, *holes) in (lng, lat)."""
    collection: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    wards = []
    for feature in collection.get("features", []):
        properties = feature.get("properties") or {}
        code = normalize_code(properties.get("NAME2")) or normalize_code(properties.get("Name"))
        geometry = feature.get("geometry") or {}
        if not code or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            continue
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        swap = _looks_lat_first(polygons[0][0][0])
        wards.append((code, tuple(tuple(_to_lng_lat(ring, swap) for ring in polygon) for polygon in polygons)))
    return tuple(wards)


def _point_in_ring(lng: float, lat: float, ring: Ring) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def find_ward(latitude: float, longitude: float) -> str | None:
    """Return the ward code containing the point, or None if it is outside every ward."""
    for code, polygons in load_wards():
        for outer, *holes in polygons:
            if _point_in_ring(longitude, latitude, outer) and not any(
                _point_in_ring(longitude, latitude, hole) for hole in holes
            ):
                return code
    return None
