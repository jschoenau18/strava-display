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

def get_rides(client : stravalib.Client, n : int) -> list:

    activity_list = []

    response = client.get_activities(limit = n)

    for act in response:

        act_name = act.name
        
        if act.start_date is not None:
            act_date = act.start_date.strftime("%d.%m.%Y")
        else: act_date = 0

        if act.distance is not None:
            act_dist = act.distance / 1000
        else:
            act_dist = 0
        act_watts = act.average_watts

        activity_list.append([act_name, act_date, act_dist, act_watts])

    return activity_list

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