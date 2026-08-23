from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "fonts"
IMG_DIR = BASE_DIR / "img"

FONT_REGULAR = str(FONTS_DIR / "Roboto-Regular.ttf")
FONT_REGULAR_CONDENSED = str(FONTS_DIR / "RobotoCondensed-Regular.ttf")
FONT_BOLD = str(FONTS_DIR / "Roboto-Bold.ttf")
FONT_BOLD_CONDENSED = str(FONTS_DIR / "RobotoCondensed-Bold.ttf")

# SPECTRA 6 COLOR PALETTE (WAVESHARE 4" E6)
BLACK, WHITE, RED, YELLOW, BLUE, GREEN = 0, 1, 2, 3, 4, 5
SPECTRA6_COLORS = [
    0,   0,   0,      # 0: Schwarz
    255, 255, 255,    # 1: Weiß
    255, 0,   0,      # 2: Rot
    255, 255, 0,      # 3: Gelb
    0,   0,   255,    # 4: Blau
    0,   255, 0,      # 5: Grün
]
SPECTRA6_COLORS = SPECTRA6_COLORS + [0] * (768 - len(SPECTRA6_COLORS))
TRANSPARENT_INDEX = 6

DISPLAY_SIZE = (600, 400)


# ENTHÄLT ZB GRÖßE, FARBEN FONTS
class Display:

    def __init__(self, size : tuple[int,int] = DISPLAY_SIZE, colors : list[int] = SPECTRA6_COLORS):

        self.size = size
        self.colors = colors

        self.image : Image.Image = Image.new('P', self.size, color = 1) #fixed color palette for e ink, white backgroud
        self.draw = ImageDraw.Draw(self.image, mode = 'P')
        self.image.putpalette(self.colors)

class GUIBox:

    """
    Rectangle with a given size (width, height).
    Anchor position at the top left (x,y).
    Background color is given as a palette index.
    """

    def __init__(self, size : tuple[int,int],
                 anchor : tuple[int,int],
                 backgroud_color : int,
                 outline_color : int | None = None,
                 outline_width : int = 2):

        """
        Backgroud color has to be selected from the color palette of the parent display
        """
        self.size = size
        self.anchor = anchor
        self.backgroud_RGB = backgroud_color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.text_list = []


    def add_text(self,
                 text : str,
                 rel_anchor : tuple[float, float],
                 text_color : int,
                 fontsize : int,
                 bold : bool = False,
                 condensed : bool = False,
                 anchor : str = "la") -> None:

        """
        anchor follows PIL's ImageDraw.text anchor convention, e.g. "la"
        (left-ascender, the default top-left placement) or "mm" (centered
        both horizontally and vertically on rel_anchor).
        """

        self.text_list.append({
            "text" : text,
            "rel_anchor" : rel_anchor,
            "fontsize" : fontsize,
            "bold" : bold,
            "condensed" : condensed,
            "text_color" : text_color,
            "anchor" : anchor,
        })

    def draw_dithered(self, draw : ImageDraw.ImageDraw, color_1, color_2, dither_count : int = 2):

        w, h = self.size
        off_x, off_y = self.anchor
        for x in range(w):
            for y in range(h):
                if(x+y)% dither_count == 0:

                    draw.point((x+off_x,y+off_y), color_1)

                else:

                    draw.point((x+off_x,y+off_y), color_2)

    def draw_box(self, draw : ImageDraw.ImageDraw) -> None:

        """
        Draws the Box according to its attributes.
        Requires a draw function to be initialized and passed (ImageDraw.draw(image))
        """

        x1, y1 = self.anchor
        x2 = x1 + self.size[0]
        y2 = y1 + self.size[1]

        draw.rectangle((x1, y1, x2, y2), self.backgroud_RGB, outline = self.outline_color, width = self.outline_width)

        # DRAW ALL THE TEXT ENTRIES

        for item in self.text_list:

            if item["bold"]:
                if item["condensed"]:

                    font = ImageFont.truetype(FONT_BOLD_CONDENSED, size = item["fontsize"])

                else:

                    font = ImageFont.truetype(FONT_BOLD, size = item["fontsize"])
            else:
                if item["condensed"]:

                    font = ImageFont.truetype(FONT_REGULAR_CONDENSED, size = item["fontsize"])

                else:

                    font = ImageFont.truetype(FONT_REGULAR, size = item["fontsize"])

            x1 = self.anchor[0] + item["rel_anchor"][0] * self.size[0]
            y1 = self.anchor[1] + item["rel_anchor"][1] * self.size[1]

            draw.text(xy = (x1,y1), text = item["text"], fill = item["text_color"], font = font, anchor = item["anchor"])

def to_spectra6(img_rgba : Image.Image, pal_img : Image.Image, transparent_index : int = TRANSPARENT_INDEX) -> Image.Image:

    alpha = img_rgba.getchannel("A")

    img_p = img_rgba.convert("RGB").quantize(palette = pal_img)

    mask = alpha.point(lambda a: 255 if a == 0 else 0)

    img_p.paste(transparent_index, mask = mask)
    img_p.info["transparency"] = transparent_index

    return img_p

def image_cleanup(image : Image.Image) -> Image.Image:

    img = image.convert("RGBA")
    img_data = img.getdata()
    new_data = []

    for pix in img_data:

        r, g, b, a = pix

        if a < 20:

            new_data.append((0,0,0,0))

        else:

            new_data.append((r,g,b,255))

    img.putdata(new_data)

    return img

def get_palette_image() -> Image.Image:

    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(SPECTRA6_COLORS)
    pal_img.info["transparency"] = TRANSPARENT_INDEX

    return pal_img

def load_logo(pal_img : Image.Image, variant : str = "white") -> Image.Image:

    logo_path = IMG_DIR / f"strava-logo-full-{variant}.png"
    logo = image_cleanup(Image.open(logo_path))

    return to_spectra6(logo, pal_img)

def paste_with_transparency(base_image : Image.Image, overlay : Image.Image, position : tuple[int,int]) -> None:

    paste_mask = overlay.point(lambda p: 0 if p == TRANSPARENT_INDEX else 255, mode = "L")
    base_image.paste(overlay, position, mask = paste_mask)

def format_duration(minutes : float) -> str:

    total_minutes = int(round(minutes))
    hours, mins = divmod(total_minutes, 60)

    if hours:
        return f"{hours}h {mins:02d}min"

    return f"{mins}min"

GERMAN_WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
GERMAN_MONTHS = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]

def format_german_date(dt : datetime) -> str:

    # Vermeidet eine Abhängigkeit von der de_DE-Systemlocale (auf dem Pi oft nicht installiert)
    weekday = GERMAN_WEEKDAYS[dt.weekday()]
    month = GERMAN_MONTHS[dt.month - 1]

    return f"{weekday}, {dt.day}. {month} {dt.year}"

def generate_greeting() -> str:

    if 6 <= datetime.now().hour < 11:

        greeting : str = "Guten Morgen"

    elif 11 <= datetime.now().hour < 18:

        greeting : str = "Guten Tag"

    elif 18 <= datetime.now().hour < 22:

        greeting : str = "Guten Abend"

    elif 22 <= datetime.now().hour < 24 or 0 <= datetime.now().hour < 6:

        greeting : str = "Gute Nacht"

    else:
        greeting : str = "Hallo"

    return greeting

# FUNKTION, DIE AUS DER MAIN AUFGERUFEN WIRD
# BRAUCHT DIE API DATEN AUS backend.api_reader.get_dashboard_data()

def make_gui(data : dict) -> Image.Image:

    display = Display()
    pal_img = get_palette_image()
    logo = load_logo(pal_img, variant = "orange")

    MARGIN = 14
    GAP = 10
    HEADER_H = 60
    LABEL_H = 22

    # HEADER (weißer Grund, dünner farbiger Akzentstreifen statt voller Farbfläche)
    header = GUIBox((display.size[0], HEADER_H), (0, 0), WHITE)

    logo_h = 30
    logo_w = int(logo_h * logo.width / logo.height)

    athlete_name = data.get("athlete_name")
    if athlete_name:
        athlete_name = athlete_name[0].upper() + athlete_name[1:]
    greeting = f"{generate_greeting()}, {athlete_name}!" if athlete_name else generate_greeting()

    text_x = (MARGIN + logo_w + 14) / header.size[0]
    header.add_text(greeting, (text_x, 0.36), BLACK, fontsize = 20, bold = True, anchor = "lm")
    header.add_text(format_german_date(datetime.now()), (text_x, 0.68), BLACK, fontsize = 12, condensed = True, anchor = "lm")
    header.draw_box(display.draw)

    display.draw.rectangle((0, HEADER_H - 3, display.size[0], HEADER_H), fill = RED)

    logo_resized = logo.resize((logo_w, logo_h))
    paste_with_transparency(display.image, logo_resized, (MARGIN, (HEADER_H - logo_h) // 2))

    # LAYOUT
    content_y = HEADER_H + GAP
    content_h = display.size[1] - content_y - MARGIN
    left_w = int((display.size[0] - 2 * MARGIN - GAP) * 0.58)
    right_x = MARGIN + left_w + GAP
    right_w = display.size[0] - MARGIN - right_x

    # LEFT COLUMN: RECENT ACTIVITIES
    recent = data.get("recent_activities") or []

    left_label = GUIBox((left_w, LABEL_H), (MARGIN, content_y), WHITE)
    left_label.add_text("LETZTE AKTIVITÄTEN", (0.5, 0.5), BLACK, fontsize = 14, bold = True, anchor = "mm")
    left_label.draw_box(display.draw)

    rows_y = content_y + LABEL_H + GAP // 2
    rows_h = content_h - LABEL_H - GAP // 2
    n_rows = max(len(recent), 1)
    row_h = (rows_h - GAP * (n_rows - 1)) // n_rows

    for i, act in enumerate(recent):

        row = GUIBox((left_w, row_h), (MARGIN, rows_y + i * (row_h + GAP)), WHITE, outline_color = BLACK)
        row.add_text(str(act.get("date", "-")), (0.5, 0.14), BLACK, fontsize = 11, condensed = True, anchor = "ma")
        row.add_text(str(act.get("name", "-"))[:26], (0.5, 0.42), BLACK, fontsize = 15, bold = True, anchor = "ma")
        row.add_text(f"{act.get('distance_km', 0):.1f} km  ·  {act.get('elevation_gain_m', 0)} hm", (0.5, 0.74), BLUE, fontsize = 12, bold = True, anchor = "ma")
        row.draw_box(display.draw)

    if not recent:
        empty_row = GUIBox((left_w, rows_h), (MARGIN, rows_y), WHITE, outline_color = BLACK)
        empty_row.add_text("Keine Aktivitäten gefunden", (0.5, 0.5), BLACK, fontsize = 13, anchor = "mm")
        empty_row.draw_box(display.draw)

    # RIGHT COLUMN: YEAR-TO-DATE STATS + LAST ACTIVITY
    ytd = data.get("ytd") or {}
    last = data.get("last_activity")

    right_label = GUIBox((right_w, LABEL_H), (right_x, content_y), WHITE)
    right_label.add_text("DIESES JAHR", (0.5, 0.5), BLACK, fontsize = 14, bold = True, anchor = "mm")
    right_label.draw_box(display.draw)

    stat_area_y = content_y + LABEL_H + GAP // 2
    stat_area_h = content_h - LABEL_H - GAP // 2
    stat_block_h = int(stat_area_h * 0.34)
    footer_h = stat_area_h - 2 * stat_block_h - 2 * GAP

    distance_block = GUIBox((right_w, stat_block_h), (right_x, stat_area_y), WHITE, outline_color = BLACK)
    distance_block.add_text("GESAMTDISTANZ", (0.5, 0.24), BLACK, fontsize = 12, bold = True, anchor = "mm")
    distance_block.add_text(f"{ytd.get('distance_km', 0):.1f} km", (0.5, 0.62), BLUE, fontsize = 24, bold = True, anchor = "mm")
    distance_block.draw_box(display.draw)

    elevation_block_y = stat_area_y + stat_block_h + GAP
    elevation_block = GUIBox((right_w, stat_block_h), (right_x, elevation_block_y), WHITE, outline_color = BLACK)
    elevation_block.add_text("HÖHENMETER", (0.5, 0.24), BLACK, fontsize = 12, bold = True, anchor = "mm")
    elevation_block.add_text(f"{ytd.get('elevation_gain_m', 0)} m", (0.5, 0.62), RED, fontsize = 24, bold = True, anchor = "mm")
    elevation_block.draw_box(display.draw)

    footer_y = elevation_block_y + stat_block_h + GAP
    footer = GUIBox((right_w, footer_h), (right_x, footer_y), WHITE, outline_color = BLACK)
    footer.add_text("LETZTE AKTIVITÄT", (0.5, 0.2), BLACK, fontsize = 11, bold = True, anchor = "mm")

    if last:
        footer.add_text(str(last.get("name", "-"))[:22], (0.5, 0.5), BLACK, fontsize = 13, bold = True, anchor = "mm")
        footer.add_text(f"{last.get('date', '-')}  ·  {last.get('distance_km', 0):.1f} km", (0.5, 0.78), BLACK, fontsize = 11, condensed = True, anchor = "mm")
    else:
        footer.add_text("Keine Aktivität", (0.5, 0.55), BLACK, fontsize = 12, anchor = "mm")

    footer.draw_box(display.draw)

    return display.image

def render_dashboard(data : dict, output_path : str | None = None) -> Image.Image:

    """
    Builds the dashboard image from the given data dict (see
    backend.api_reader.get_dashboard_data) and optionally saves it to disk.
    """

    image = make_gui(data)

    if output_path is not None:
        image.convert("RGB").save(output_path)

    return image

if __name__ == "__main__":

    # DUMMY-DATEN ZUM TESTEN DES RENDERINGS OHNE STRAVA-API
    dummy_data = {
        "athlete_name": "Johannes",
        "ytd": {
            "distance_km": 1243.7,
            "moving_time_min": 5310,
            "elevation_gain_m": 15200,
            "activity_count": 87,
        },
        "last_activity": {
            "name": "Feierabendrunde",
            "date": "22.08.2026",
            "sport_type": "Ride",
            "distance_km": 42.1,
            "moving_time_min": 95,
            "elevation_gain_m": 620,
            "average_watts": 187,
        },
        "recent_activities": [
            {"name": "Feierabendrunde", "date": "22.08.2026", "distance_km": 42.1, "elevation_gain_m": 620},
            {"name": "Sonntags-Runde", "date": "17.08.2026", "distance_km": 65.4, "elevation_gain_m": 1200},
            {"name": "Trail-Abenteuer", "date": "15.08.2026", "distance_km": 31.8, "elevation_gain_m": 1100},
            {"name": "Nachtlauf", "date": "13.08.2026", "distance_km": 8.4, "elevation_gain_m": 90},
        ],
    }

    dashboard_image = render_dashboard(dummy_data)
    dashboard_image.show()
