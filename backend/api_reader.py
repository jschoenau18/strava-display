import stravalib
from dotenv import set_key
import os
from datetime import datetime, timedelta
from backend.geodata import get_map_features


def api_setup(dotenv_path : str) -> None:

    if not "STRAVA_CLIENT_ID" in os.environ:

        print("Add Client-ID and Client Secret to .env file!")

    client_id = int(str(os.getenv(key = "STRAVA_CLIENT_ID")))
    client_secret = str(os.getenv(key = "STRAVA_CLIENT_SECRET"))
    client = stravalib.Client()
    auth_url : str = client.authorization_url(client_id = client_id,
                                        redirect_uri = "http://localhost:8000",
                                        scope = ['profile:read_all', 'activity:read_all'])
    
    print(f"Click the following URL: {auth_url}")
    auth_code = input("Paste the code here:\n")

    token_response = client.exchange_code_for_token(client_id = client_id,
                                                client_secret = client_secret,
                                                code = auth_code,
                                                return_athlete = False)
    # exchange_code_for_token may return an AccessInfo object or a tuple
    # (AccessInfo, SummaryAthlete|None). Normalize to access_info dict-like object.
    if isinstance(token_response, tuple):
        access_info = token_response[0]
    else:
        access_info = token_response
    
    print("✅ Benutzer verbunden!")
    
    # Access fields from AccessInfo attributes
    access_token = getattr(access_info, 'access_token', None) or access_info.get('access_token')
    refresh_token = getattr(access_info, 'refresh_token', None) or access_info.get('refresh_token')
    expires_at = getattr(access_info, 'expires_at', None) or access_info.get('expires_at')

    set_key(dotenv_path, "STRAVA_ACCESS_TOKEN", str(access_token))
    set_key(dotenv_path, "STRAVA_REFRESH_TOKEN", str(refresh_token))
    set_key(dotenv_path, "STRAVA_EXPIRES_AT", str(expires_at))

    print("✅ Tokens erfolgreich in .env gespeichert!")

    client.access_token = access_token
    athlete = client.get_athlete()
    print(f"Erfolgreich verbunden mit dem Profil von: {athlete.firstname} {athlete.lastname}")

def refresh_api_access(dotenv_path : str):

    client = stravalib.Client()
    client_id = int(str(os.getenv("STRAVA_CLIENT_ID")))
    client_secret = str(os.getenv("STRAVA_CLIENT_SECRET"))
    refresh_token = str(os.getenv("STRAVA_REFRESH_TOKEN"))

    token_response = client.refresh_access_token(client_id = client_id,
                                                 client_secret = client_secret,
                                                 refresh_token = refresh_token)
    
    print("✅ Neues Token empfangen!")


    set_key(dotenv_path = dotenv_path,
                key_to_set = "STRAVA_ACCESS_TOKEN",
                value_to_set = token_response.get("access_token"))
        
    set_key(dotenv_path = dotenv_path,
                key_to_set = "STRAVA_EXPIRES_AT",
                value_to_set = str(token_response.get("expires_at")))

    print("✅ Neues Token gespeichert!")

def _duration_seconds(duration) -> float:

    """
    stravalib <2.0 represents durations as datetime.timedelta, >=2.0 as an
    int-like Duration (raw seconds). Handle both.
    """

    if duration is None:
        return 0.0

    if hasattr(duration, "total_seconds"):
        return duration.total_seconds()

    return float(duration)

def _activity_to_dict(act) -> dict:

    return {
        "id": act.id,
        "name": act.name,
        "date": act.start_date_local.strftime("%d.%m.%Y") if act.start_date_local else None,
        "sport_type": str(act.sport_type) if act.sport_type else None,
        "distance_km": round(float(act.distance) / 1000, 1) if act.distance is not None else 0.0,
        "moving_time_min": round(_duration_seconds(act.moving_time) / 60),
        "elevation_gain_m": round(float(act.total_elevation_gain)) if act.total_elevation_gain is not None else 0,
        "average_watts": round(act.average_watts) if act.average_watts is not None else None,
        "average_speed_kmh": round(float(act.average_speed) * 3.6, 1) if act.average_speed is not None else None,
        "kudos_count": int(act.kudos_count or 0),
    }

def get_recent_activities(client : stravalib.Client, n : int) -> list[dict]:

    """
    Returns a summary dict for each of the last n activities, most recent first.
    """

    return [_activity_to_dict(act) for act in client.get_activities(limit = n)]

def get_weekly_cycling_distance(client : stravalib.Client, weeks : int = 6) -> list[dict]:

    """
    Returns cycling distance grouped by Monday-to-Sunday week, oldest first.
    """

    today = datetime.now().date()
    current_week = today - timedelta(days = today.weekday())
    first_week = current_week - timedelta(weeks = weeks - 1)
    distances = {first_week + timedelta(weeks = i): 0.0 for i in range(weeks)}
    after = datetime.combine(first_week, datetime.min.time())
    cycling_sports = {
        "Ride", "VirtualRide", "GravelRide", "MountainBikeRide",
        "EMountainBikeRide", "EBikeRide", "Velomobile", "Handcycle",
    }

    for activity in client.get_activities(after = after):
        sport_type = getattr(activity.sport_type, "root", str(activity.sport_type))
        if activity.start_date_local is None or sport_type not in cycling_sports:
            continue

        activity_week = activity.start_date_local.date() - timedelta(days = activity.start_date_local.weekday())
        if activity_week in distances and activity.distance is not None:
            distances[activity_week] += float(activity.distance) / 1000

    return [
        {"label": week.strftime("%d.%m."), "distance_km": round(distance, 1)}
        for week, distance in distances.items()
    ]

def get_last_activity_route(streams : dict) -> list[tuple[float, float, float | None]]:

    """
    Returns the GPS track of an activity as a list of (lat, lon,
    elevation_m) points, read from its latlng and altitude streams
    (see get_activity_streams()). elevation_m is
    None if no altitude data exists for that point (e.g. an indoor or
    GPS-only recording).
    """

    latlng_stream = streams.get("latlng") if streams else None
    if latlng_stream is None:
        return []

    altitude_stream = streams.get("altitude") if streams else None
    altitudes = altitude_stream.data if altitude_stream is not None else None

    return [
        (lat, lon, altitudes[i] if altitudes is not None and i < len(altitudes) else None)
        for i, (lat, lon) in enumerate(latlng_stream.data)
    ]

def get_ytd_stats(client : stravalib.Client) -> dict:

    """
    Returns year-to-date totals across rides, runs and swims combined.
    """

    stats = client.get_athlete_stats()
    totals = [stats.ytd_ride_totals, stats.ytd_run_totals, stats.ytd_swim_totals]

    distance_km = 0.0
    moving_time_min = 0.0
    elevation_gain_m = 0.0
    activity_count = 0

    for total in totals:

        if total is None:
            continue

        if total.distance is not None:
            distance_km += float(total.distance) / 1000

        if total.moving_time is not None:
            moving_time_min += _duration_seconds(total.moving_time) / 60

        if total.elevation_gain is not None:
            elevation_gain_m += float(total.elevation_gain)

        if total.count is not None:
            activity_count += total.count

    return {
        "distance_km": round(distance_km, 1),
        "moving_time_min": round(moving_time_min),
        "elevation_gain_m": round(elevation_gain_m),
        "activity_count": activity_count,
    }

def get_athlete_name(client : stravalib.Client) -> str:

    athlete = client.get_athlete()

    return athlete.firstname or ""

def get_activity_streams(client : stravalib.Client, activity_id : int) -> dict:

    """
    Fetches every stream the dashboard needs (GPS track, altitude,
    time, power) for one activity in a single API call, so callers
    like get_last_activity_route() and get_best_power_efforts() don't
    each make their own round trip for the same activity.
    """

    return client.get_activity_streams(activity_id, types = ["latlng", "altitude", "time", "watts"])

def _best_avg_power(times : list[float], watts : list[float], window_seconds : int) -> float | None:

    """
    Sliding-window scan (by elapsed time, not sample count, since stream
    sampling isn't always exactly 1Hz) for the highest average power
    over the given window length. Returns None if the activity doesn't
    reach that duration.
    """

    if not times or not watts:
        return None

    best_avg = None
    left = 0
    running_sum = 0.0

    for right in range(len(times)):

        running_sum += watts[right]

        while times[right] - times[left] > window_seconds:
            running_sum -= watts[left]
            left += 1

        elapsed = times[right] - times[left]
        if elapsed >= window_seconds - 1:
            avg = running_sum / (right - left + 1)
            if best_avg is None or avg > best_avg:
                best_avg = avg

    return best_avg

def get_best_power_efforts(streams : dict, durations_min : tuple[int, ...] = (60, 20, 5)) -> dict:

    """
    Returns the best average power (W) for each given duration in
    minutes, keyed by duration, read from an activity's time and watts
    streams (see get_activity_streams_for_last_activity()). None for a
    duration the activity doesn't reach, or if there's no power data.
    """

    time_stream = streams.get("time") if streams else None
    watts_stream = streams.get("watts") if streams else None

    if time_stream is None or watts_stream is None:
        return {d: None for d in durations_min}

    return {
        d: round(best_avg) if (best_avg := _best_avg_power(time_stream.data, watts_stream.data, d * 60)) is not None else None
        for d in durations_min
    }

def get_power_metrics(streams : dict, average_power : int | float | None) -> dict:

    """Return average power, normalized power and the best 3-second power."""

    time_stream = streams.get("time") if streams else None
    watts_stream = streams.get("watts") if streams else None
    if time_stream is None or watts_stream is None:
        return {
            "average_power": round(average_power) if average_power is not None else None,
            "normalized_power": None,
            "top_power_3s": None,
        }

    times = time_stream.data
    watts = watts_stream.data
    sample_count = min(len(times), len(watts))
    if sample_count == 0:
        return {
            "average_power": round(average_power) if average_power is not None else None,
            "normalized_power": None,
            "top_power_3s": None,
        }

    times = times[:sample_count]
    watts = [float(watt) for watt in watts[:sample_count]]
    rolling_sum = 0.0
    left = 0
    rolling_fourths = []

    for right, timestamp in enumerate(times):
        rolling_sum += watts[right]
        while timestamp - times[left] > 30:
            rolling_sum -= watts[left]
            left += 1
        rolling_average = rolling_sum / (right - left + 1)
        rolling_fourths.append(rolling_average ** 4)

    normalized_power = round((sum(rolling_fourths) / len(rolling_fourths)) ** 0.25)
    top_power_3s = _best_avg_power(times, watts, 3)

    return {
        "average_power": round(average_power) if average_power is not None else None,
        "normalized_power": round(normalized_power),
        "top_power_3s": round(top_power_3s) if top_power_3s is not None else None,
    }

def get_dashboard_data(client : stravalib.Client, n_recent : int = 1) -> dict:

    """
    Pulls and calculates everything the display needs in one call.
    """

    recent_activities = get_recent_activities(client, n_recent)
    last_activity = recent_activities[0] if recent_activities else None

    streams = get_activity_streams(client, last_activity["id"]) if last_activity else {}
    last_activity_route = get_last_activity_route(streams)

    return {
        "athlete_name": get_athlete_name(client),
        "ytd": get_ytd_stats(client),
        "last_activity": last_activity,
        "recent_activities": recent_activities,
        "weekly_cycling_distance": get_weekly_cycling_distance(client),
        "last_activity_route": last_activity_route,
        "best_power_efforts": get_best_power_efforts(streams),
        "power_metrics": get_power_metrics(streams, last_activity.get("average_watts") if last_activity else None),
        "map_features": get_map_features(last_activity_route),
    }
