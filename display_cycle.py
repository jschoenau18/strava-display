from dotenv import load_dotenv
import os
from display.display import TOTAL_PAGES
from display.eink import update_display_from_file

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output")
PAGE_STATE_PATH = os.path.join(CURRENT_DIR, ".display_page_state")


def page_output_path(page : int) -> str:

    return os.path.join(OUTPUT_DIR, f"dashboard_page{page}.png")


def next_page(total_pages : int) -> int:

    """
    Alternates between the pages main.py rendered (1-indexed), so
    repeated runs of this script cycle the e-paper display through them
    over time. Persists the last shown page to disk since each run is a
    fresh process. Always returns 1 if total_pages is 1 (STRAVA_SHOW_PAGE2=0).
    """

    try:
        with open(PAGE_STATE_PATH, "r") as state_file:
            last_page = int(state_file.read().strip())
    except (OSError, ValueError):
        last_page = 0

    page = last_page % total_pages + 1

    with open(PAGE_STATE_PATH, "w") as state_file:
        state_file.write(str(page))

    return page


if __name__ == "__main__":

    load_dotenv(dotenv_path = os.path.join(CURRENT_DIR, ".env"))

    # Derselbe Schalter wie in main.py: bei STRAVA_SHOW_PAGE2=0 wird immer
    # nur Seite 1 gezeigt, unabhängig davon, ob noch eine alte
    # dashboard_page2.png von main.py existiert.
    total_pages = TOTAL_PAGES if os.getenv("STRAVA_SHOW_PAGE2", "1") == "1" else 1

    page = next_page(total_pages)
    page_path = page_output_path(page)

    if not os.path.exists(page_path):
        print(f"❌ {page_path} existiert noch nicht - main.py muss zuerst laufen.")

    elif os.getenv("STRAVA_UPDATE_DISPLAY", "0") == "1":
        update_display_from_file(page_path)
        print(f"✅ E-Paper-Display auf Seite {page} aktualisiert ({page_path})!")

    else:
        print(f"ℹ️ STRAVA_UPDATE_DISPLAY ist nicht gesetzt, überspringe Anzeige von Seite {page}.")
