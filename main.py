import stravalib
from dotenv import load_dotenv
import os
import time
from backend.api_reader import api_setup, refresh_api_access, get_dashboard_data
from backend.version import get_release_label
from display.display import render_dashboard, TOTAL_PAGES

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def page_output_path(page : int) -> str:

    return os.path.join(OUTPUT_DIR, f"dashboard_page{page}.png")

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

    # STRAVA_SHOW_PAGE2=0 rendert nur Seite 1 (kein Seiten-Indikator, siehe
    # display.make_gui). display_cycle.py liest denselben Schalter und
    # zeigt dann dauerhaft nur Seite 1 an.
    total_pages = TOTAL_PAGES if os.getenv("STRAVA_SHOW_PAGE2", "1") == "1" else 1
    page_output_paths = [page_output_path(page) for page in range(1, total_pages + 1)]

    os.makedirs(OUTPUT_DIR, exist_ok = True)
    for page, output_path in enumerate(page_output_paths, start = 1):
        render_dashboard(dashboard_data, output_path = output_path, page = page, total_pages = total_pages)

    # Verwaiste Seiten von einem früheren Lauf mit mehr Seiten entfernen,
    # damit display_cycle.py nie ein veraltetes Bild anzeigt.
    for page in range(total_pages + 1, TOTAL_PAGES + 1):
        stale_path = page_output_path(page)
        if os.path.exists(stale_path):
            os.remove(stale_path)

    # display_cycle.py läuft alle 2 Minuten separat und wechselt zwischen
    # den hier gerenderten Seiten hin und her (siehe dort).
    print(f"✅ Dashboard-Seiten gerendert: {', '.join(page_output_paths)}")
