import stravalib
from dotenv import load_dotenv
import os
import time
from backend.api_reader import api_setup, refresh_api_access, get_dashboard_data
from backend.version import get_release_label
from display.display import render_dashboard
from display.eink import update_display_from_file

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "dashboard.png")

if __name__ == "__main__":

    current_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(current_dir, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    if "STRAVA_EXPIRES_AT" in os.environ:
        print("✅ Benutzer verbunden!")

    else:

        print(f"❌ Kein Konto verbunden. Beginne Setup...")
        api_setup(dotenv_path)
        load_dotenv(dotenv_path=dotenv_path)

    expires_at = os.getenv("STRAVA_EXPIRES_AT")
    if expires_at and int(time.time()) > int(expires_at):

        print("❌ Access Token expired! Refreshe...")
        refresh_api_access(dotenv_path)
        load_dotenv(dotenv_path=dotenv_path)

    else:

        print("✅ Token gültig!")

    client = stravalib.Client(access_token = str(os.getenv("STRAVA_ACCESS_TOKEN")),
                              refresh_token = str(os.getenv("STRAVA_REFRESH_TOKEN")),
                              token_expires = int(str(os.getenv("STRAVA_EXPIRES_AT"))))

    dashboard_data = get_dashboard_data(client)
    dashboard_data["release_label"] = get_release_label()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok = True)
    render_dashboard(dashboard_data, output_path = OUTPUT_PATH)

    if os.getenv("STRAVA_UPDATE_DISPLAY", "0") == "1":
        update_display_from_file(OUTPUT_PATH)
        print("✅ E-Paper-Display aktualisiert!")

    print(f"✅ Dashboard gerendert: {OUTPUT_PATH}")