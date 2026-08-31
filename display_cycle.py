from dotenv import load_dotenv
import os
from display.display import TOTAL_PAGES
from display.eink import update_display_from_file

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output")
PAGE_OUTPUT_PATHS = [os.path.join(OUTPUT_DIR, f"dashboard_page{page}.png") for page in range(1, TOTAL_PAGES + 1)]
PAGE_STATE_PATH = os.path.join(CURRENT_DIR, ".display_page_state")


def next_page() -> int:

    """
    Alternates between the pages main.py rendered (1-indexed), so
    repeated runs of this script cycle the e-paper display through them
    over time. Persists the last shown page to disk since each run is a
    fresh process.
    """

    try:
        with open(PAGE_STATE_PATH, "r") as state_file:
            last_page = int(state_file.read().strip())
    except (OSError, ValueError):
        last_page = 0

    page = last_page % TOTAL_PAGES + 1

    with open(PAGE_STATE_PATH, "w") as state_file:
        state_file.write(str(page))

    return page


if __name__ == "__main__":

    load_dotenv(dotenv_path = os.path.join(CURRENT_DIR, ".env"))

    page = next_page()
    page_path = PAGE_OUTPUT_PATHS[page - 1]

    if not os.path.exists(page_path):
        print(f"❌ {page_path} existiert noch nicht - main.py muss zuerst laufen.")

    elif os.getenv("STRAVA_UPDATE_DISPLAY", "0") == "1":
        update_display_from_file(page_path)
        print(f"✅ E-Paper-Display auf Seite {page} aktualisiert ({page_path})!")

    else:
        print(f"ℹ️ STRAVA_UPDATE_DISPLAY ist nicht gesetzt, überspringe Anzeige von Seite {page}.")
