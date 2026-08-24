from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parent.parent / "output" / "geodata-cache"
GRID_SIZE = 9
CONTOUR_INTERVAL_M = 50

# WIDTH:HEIGHT DER ROUTEN-KARTE IN display.make_gui() (LINKE SPALTE MINUS
# HOEHEN-LEGENDE). display.py SKALIERT DIE ROUTE SO, DASS SIE DIESES
# SEITENVERHAELTNIS AUSFUELLT (SIEHE _route_projection) - WUERDE DIE BBOX HIER
# NICHT DASSELBE VERHAELTNIS TREFFEN, REICHEN HOEHENLINIEN/FLUESSE NACH DEM
# SKALIEREN NIE BIS AN DEN RAND EINER SCHMALEN (Z.B. NORD-SUED-) ROUTE.
ROUTE_CARD_ASPECT = 289 / 181


def _cache_path(prefix: str, bbox: tuple[float, float, float, float]) -> Path:
    key = ",".join(f"{value:.4f}" for value in bbox)
    digest = hashlib.sha1(key.encode("ascii")).hexdigest()[:16]
    return CACHE_DIR / f"{prefix}-{digest}.json"


def _fetch_json(url: str, timeout: int = 12) -> dict:
    request = Request(url, headers={"User-Agent": "strava-api-display/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _route_bbox(route: list[tuple], padding: float = 0.002) -> tuple[float, float, float, float] | None:
    if not route:
        return None

    latitudes = [point[0] for point in route]
    longitudes = [point[1] for point in route]
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)

    lat_mid_rad = math.radians((min_lat + max_lat) / 2)
    cos_lat = math.cos(lat_mid_rad) or 1e-9
    lat_range = (max_lat - min_lat) or 1e-6
    lon_range_corrected = ((max_lon - min_lon) or 1e-6) * cos_lat

    # KUERZERE ACHSE AUFWEITEN, BIS DIE BBOX DAS SEITENVERHAELTNIS DER
    # ANZEIGE-KARTE TRIFFT (SIEHE ROUTE_CARD_ASPECT), STATT NUR DER ROUTE
    # SELBST ZU FOLGEN.
    if lon_range_corrected / lat_range < ROUTE_CARD_ASPECT:
        target_lon_range = (ROUTE_CARD_ASPECT * lat_range) / cos_lat
        center_lon = (min_lon + max_lon) / 2
        min_lon, max_lon = center_lon - target_lon_range / 2, center_lon + target_lon_range / 2
    else:
        target_lat_range = lon_range_corrected / ROUTE_CARD_ASPECT
        center_lat = (min_lat + max_lat) / 2
        min_lat, max_lat = center_lat - target_lat_range / 2, center_lat + target_lat_range / 2

    return (
        min_lat - padding,
        min_lon - padding,
        max_lat + padding,
        max_lon + padding,
    )


def _grid_points(bbox: tuple[float, float, float, float]) -> list[tuple[float, float]]:
    min_lat, min_lon, max_lat, max_lon = bbox
    return [
        (
            min_lat + (max_lat - min_lat) * row / (GRID_SIZE - 1),
            min_lon + (max_lon - min_lon) * column / (GRID_SIZE - 1),
        )
        for row in range(GRID_SIZE)
        for column in range(GRID_SIZE)
    ]


def _load_elevation_grid(bbox: tuple[float, float, float, float]) -> list[list[float]]:
    cache_path = _cache_path("elevation", bbox)
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    points = _grid_points(bbox)
    locations = "|".join(f"{lat:.5f},{lon:.5f}" for lat, lon in points)
    response = _fetch_json(f"https://api.opentopodata.org/v1/aster30m?locations={quote(locations)}")
    elevations = [result.get("elevation") for result in response.get("results", [])]
    if len(elevations) != len(points) or any(value is None for value in elevations):
        raise RuntimeError("Höhendaten unvollständig")

    grid = [elevations[row * GRID_SIZE:(row + 1) * GRID_SIZE] for row in range(GRID_SIZE)]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(grid))
    return grid


def _interpolate(point_a: tuple[float, float], value_a: float,
                 point_b: tuple[float, float], value_b: float,
                 level: float) -> tuple[float, float]:
    if value_a == value_b:
        factor = 0.5
    else:
        factor = (level - value_a) / (value_b - value_a)
    factor = max(0.0, min(1.0, factor))
    return (
        point_a[0] + (point_b[0] - point_a[0]) * factor,
        point_a[1] + (point_b[1] - point_a[1]) * factor,
    )


def _contour_segments(bbox: tuple[float, float, float, float], grid: list[list[float]]) -> list[list[tuple[float, float]]]:
    min_lat, min_lon, max_lat, max_lon = bbox
    lat_step = (max_lat - min_lat) / (GRID_SIZE - 1)
    lon_step = (max_lon - min_lon) / (GRID_SIZE - 1)
    minimum = min(min(row) for row in grid)
    maximum = max(max(row) for row in grid)
    first_level = math.ceil(minimum / CONTOUR_INTERVAL_M) * CONTOUR_INTERVAL_M
    segments = []

    for level in range(first_level, math.floor(maximum) + 1, CONTOUR_INTERVAL_M):
        for row in range(GRID_SIZE - 1):
            for column in range(GRID_SIZE - 1):
                corners = [
                    ((min_lat + row * lat_step, min_lon + column * lon_step), grid[row][column]),
                    ((min_lat + (row + 1) * lat_step, min_lon + column * lon_step), grid[row + 1][column]),
                    ((min_lat + (row + 1) * lat_step, min_lon + (column + 1) * lon_step), grid[row + 1][column + 1]),
                    ((min_lat + row * lat_step, min_lon + (column + 1) * lon_step), grid[row][column + 1]),
                ]
                crossings = []
                for index in range(4):
                    first, second = corners[index], corners[(index + 1) % 4]
                    if (first[1] < level) != (second[1] < level):
                        crossings.append(_interpolate(first[0], first[1], second[0], second[1], level))
                if len(crossings) == 2:
                    segments.append(crossings)
                elif len(crossings) == 4:
                    segments.extend((crossings[:2], crossings[2:]))

    return segments


def _load_rivers(bbox: tuple[float, float, float, float]) -> list[list[tuple[float, float]]]:
    cache_path = _cache_path("rivers", bbox)
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    min_lat, min_lon, max_lat, max_lon = bbox
    query = (
        f"[out:json][timeout:10];way[\"waterway\"~\"^(river|canal)$\"]"
        f"({min_lat},{min_lon},{max_lat},{max_lon});out geom;"
    )
    response = _fetch_json(f"https://overpass-api.de/api/interpreter?data={quote(query)}")
    rivers = [
        [(point["lat"], point["lon"]) for point in element.get("geometry", [])]
        for element in response.get("elements", [])
        if len(element.get("geometry", [])) >= 2
    ]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(rivers))
    return rivers


def get_map_features(route: list[tuple]) -> dict[str, list[list[tuple[float, float]]]]:
    bbox = _route_bbox(route)
    if bbox is None:
        return {"contours": [], "rivers": []}

    try:
        contours = _contour_segments(bbox, _load_elevation_grid(bbox))
    except Exception:
        contours = []

    try:
        rivers = _load_rivers(bbox)
    except Exception:
        rivers = []

    return {"contours": contours, "rivers": rivers}
