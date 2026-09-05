from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_PATH = Path(__file__).resolve().parent.parent / "output" / "weather-location.json"


def _fetch_weather(latitude: float, longitude: float) -> dict:
    query = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m",
        "minutely_15": "precipitation,precipitation_probability",
        "forecast_minutely_15": 4,
        "forecast_days": 1,
        "timezone": "auto",
    })
    request = Request(
        f"https://api.open-meteo.com/v1/forecast?{query}",
        headers={"User-Agent": "strava-api-display/1.0"},
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def _pi_location(route: list[tuple]) -> tuple[float, float] | None:
    configured_latitude = os.getenv("WEATHER_LATITUDE")
    configured_longitude = os.getenv("WEATHER_LONGITUDE")
    if configured_latitude and configured_longitude:
        return float(configured_latitude), float(configured_longitude)

    if CACHE_PATH.exists() and time.time() - CACHE_PATH.stat().st_mtime < 86400:
        try:
            location = json.loads(CACHE_PATH.read_text())
            return float(location["latitude"]), float(location["longitude"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            pass

    try:
        request = Request("https://ipapi.co/json/", headers={"User-Agent": "strava-api-display/1.0"})
        with urlopen(request, timeout=5) as response:
            location = json.load(response)
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = CACHE_PATH.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps({"latitude": latitude, "longitude": longitude}))
        tmp_path.replace(CACHE_PATH)
        return latitude, longitude
    except (KeyError, TypeError, ValueError, OSError):
        return route[-1][:2] if route else None


def get_weather(route: list[tuple]) -> dict:
    location = _pi_location(route)
    if location is None:
        return {}

    try:
        latitude, longitude = location
        response = _fetch_weather(latitude, longitude)
        current = response.get("current", {})
        minutely = response.get("minutely_15", {})
        precipitation = [float(value or 0) for value in minutely.get("precipitation", [])[:2]]
        probability = [float(value or 0) for value in minutely.get("precipitation_probability", [])[:2]]
        rain_amount = max(precipitation, default=0)
        rain_probability = max(probability, default=0)

        if rain_amount >= 0.5 or rain_probability >= 70:
            precipitation_state = "rain"
        elif rain_amount > 0 or rain_probability >= 30:
            precipitation_state = "showers"
        else:
            precipitation_state = "clear"

        return {
            "temperature": round(float(current["temperature_2m"])),
            "wind_speed": round(float(current["wind_speed_10m"])),
            "wind_direction_deg": float(current["wind_direction_10m"]),
            "precipitation_state": precipitation_state,
        }
    except (KeyError, TypeError, ValueError, OSError):
        return {}
