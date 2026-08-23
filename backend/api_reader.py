import stravalib 
from dotenv import set_key
import os
from datetime import datetime
import polyline
import gpxpy
import gpxpy.gpx
from pathlib import Path
import re


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
        "name": act.name,
        "date": act.start_date_local.strftime("%d.%m.%Y") if act.start_date_local else None,
        "sport_type": str(act.sport_type) if act.sport_type else None,
        "distance_km": round(float(act.distance) / 1000, 1) if act.distance is not None else 0.0,
        "moving_time_min": round(_duration_seconds(act.moving_time) / 60),
        "elevation_gain_m": round(float(act.total_elevation_gain)) if act.total_elevation_gain is not None else 0,
        "average_watts": round(act.average_watts) if act.average_watts is not None else None,
    }

def get_recent_activities(client : stravalib.Client, n : int) -> list[dict]:

    """
    Returns a summary dict for each of the last n activities, most recent first.
    """

    return [_activity_to_dict(act) for act in client.get_activities(limit = n)]

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

def get_dashboard_data(client : stravalib.Client, n_recent : int = 4) -> dict:

    """
    Pulls and calculates everything the display needs in one call.
    """

    recent_activities = get_recent_activities(client, n_recent)

    return {
        "athlete_name": get_athlete_name(client),
        "ytd": get_ytd_stats(client),
        "last_activity": recent_activities[0] if recent_activities else None,
        "recent_activities": recent_activities,
    }

def segment_gpx(client : stravalib.Client, segment_id : int) -> None:
    
    gpx_output_dir = Path(__file__).resolve().parent.parent / "gpx-output"
    gpx_output_dir.mkdir(parents = True, exist_ok = True)

    seg = client.get_segment(segment_id = segment_id)
    if seg.map is None or seg.map.polyline is None:
        raise ValueError(f"Segment {segment_id} has no map polyline data")

    polyline_str = seg.map.polyline
    coors = polyline.decode(polyline_str)

    gpx = gpxpy.gpx.GPX()

    gpx_track = gpxpy.gpx.GPXTrack(name = seg.name)
    gpx.tracks.append(gpx_track)

    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for lat,long in coors:
        trackpoint = gpxpy.gpx.GPXTrackPoint(latitude = lat, longitude = long)
        gpx_segment.points.append(trackpoint)
    
    segment_name = seg.name or "segment"
    safe_name = re.sub(r'[\\/*?:"<> |]', '_', segment_name)
    filename = gpx_output_dir / f"{safe_name}.gpx"

    with open(filename, "w", encoding = "utf-8") as gpx_file:
        gpx_file.write(gpx.to_xml())