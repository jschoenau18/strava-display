from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
import math

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

EARTH_CIRCUMFERENCE_KM = 40075
EVEREST_HEIGHT_M = 8849


# ENTHÄLT ZB GRÖßE, FARBEN FONTS
class Display:

    def __init__(self, size : tuple[int,int] = DISPLAY_SIZE, colors : list[int] = SPECTRA6_COLORS):

        self.size = size
        self.colors = colors

        self.image : Image.Image = Image.new('P', self.size, color = 1) #fixed color palette for e ink, white backgroud
        self.draw = ImageDraw.Draw(self.image, mode = 'P')
        self.image.putpalette(self.colors)

def _select_font(fontsize : int, bold : bool, condensed : bool) -> ImageFont.FreeTypeFont:

    if bold:
        return ImageFont.truetype(FONT_BOLD_CONDENSED if condensed else FONT_BOLD, size = fontsize)

    return ImageFont.truetype(FONT_REGULAR_CONDENSED if condensed else FONT_REGULAR, size = fontsize)

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

            font = _select_font(item["fontsize"], item["bold"], item["condensed"])

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

def load_icon(pal_img : Image.Image, filename : str) -> Image.Image:

    icon_path = IMG_DIR / filename
    icon = image_cleanup(Image.open(icon_path))

    return to_spectra6(icon, pal_img)

def load_logo(pal_img : Image.Image, variant : str = "white") -> Image.Image:

    return load_icon(pal_img, f"strava-logo-full-{variant}.png")

def paste_with_transparency(base_image : Image.Image, overlay : Image.Image, position : tuple[int,int]) -> None:

    paste_mask = overlay.point(lambda p: 0 if p == TRANSPARENT_INDEX else 255, mode = "L")
    base_image.paste(overlay, position, mask = paste_mask)

def draw_light_divider(display : Display, center_x : float, y : int, width : int, thickness : int = 3) -> None:

    """
    Draws a light-gray dithered divider bar (same technique as the
    header accent line) centered horizontally on center_x.
    """

    divider = GUIBox((width, thickness), (int(center_x - width / 2), y), WHITE)
    divider.draw_dithered(display.draw, BLACK, WHITE, dither_count = 2)

def draw_icon_value(display : Display,
                     icon : Image.Image,
                     anchor : tuple[float, float],
                     icon_h : int,
                     text : str,
                     text_color : int,
                     fontsize : int,
                     gap : int = 6,
                     center_in_width : float | None = None) -> None:

    """
    Pastes icon (scaled to icon_h) at anchor, then draws text vertically
    centered to its right. Used for the small icon+value stat chips.
    If center_in_width is given, the whole icon+text group is centered
    within that width instead of starting exactly at anchor.
    """

    icon_w = int(icon_h * icon.width / icon.height)
    font = ImageFont.truetype(FONT_BOLD_CONDENSED, size = fontsize)
    text_w = font.getlength(text)

    x, y = anchor
    if center_in_width is not None:
        x += (center_in_width - (icon_w + gap + text_w)) / 2

    icon_resized = icon.resize((icon_w, icon_h))
    paste_with_transparency(display.image, icon_resized, (int(x), int(y)))

    text_x = x + icon_w + gap
    text_y = y + icon_h / 2
    display.draw.text((text_x, text_y), text, fill = text_color, font = font, anchor = "lm")

def _project_route_points(points : list[tuple],
                           box_size : tuple[int, int],
                           padding : int = 6) -> list[tuple[float, float]]:

    """
    Projects (lat, lon, ...) GPS points onto pixel coordinates that fit
    inside box_size while preserving the route's real-world aspect
    ratio. Any extra tuple elements (e.g. elevation) are ignored.
    """

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # LÄNGENGRAD-ABSTÄNDE SCHRUMPFEN MIT COS(BREITENGRAD) -> FÜR RICHTIGES SEITENVERHÄLTNIS KORRIGIEREN
    lat_mid_rad = math.radians((min_lat + max_lat) / 2)
    lon_range = (max_lon - min_lon) * math.cos(lat_mid_rad) or 1e-9
    lat_range = (max_lat - min_lat) or 1e-9

    avail_w = box_size[0] - 2 * padding
    avail_h = box_size[1] - 2 * padding
    scale = min(avail_w / lon_range, avail_h / lat_range)

    drawn_w = lon_range * scale
    drawn_h = lat_range * scale
    offset_x = padding + (avail_w - drawn_w) / 2
    offset_y = padding + (avail_h - drawn_h) / 2

    pixel_points = []
    for p in points:
        x = offset_x + (p[1] - min_lon) * math.cos(lat_mid_rad) * scale
        y = offset_y + (max_lat - p[0]) * scale  # BILD-Y WÄCHST NACH UNTEN, BREITENGRAD NACH OBEN
        pixel_points.append((x, y))

    return pixel_points

STRAVA_ORANGE = (252, 76, 2, 255)

ELEVATION_HEATMAP_STOPS = [
    (0.00, (40, 70, 200)),    # NIEDRIG: BLAU
    (0.35, (0, 170, 90)),     # GRÜN
    (0.7, (240, 200, 20)),    # GELB
    (1.00, (220, 30, 20)),    # HOCH: ROT
]

def _elevation_color(t : float) -> tuple[int, int, int, int]:

    """
    Maps a normalized elevation (0 = route minimum, 1 = route maximum)
    to an RGBA heatmap color, interpolated across ELEVATION_HEATMAP_STOPS.
    """

    t = max(0.0, min(1.0, t))

    for (t0, c0), (t1, c1) in zip(ELEVATION_HEATMAP_STOPS, ELEVATION_HEATMAP_STOPS[1:]):
        if t <= t1:
            local_t = (t - t0) / (t1 - t0) if t1 > t0 else 0
            r = round(c0[0] + (c1[0] - c0[0]) * local_t)
            g = round(c0[1] + (c1[1] - c0[1]) * local_t)
            b = round(c0[2] + (c1[2] - c0[2]) * local_t)
            return (r, g, b, 255)

    return (*ELEVATION_HEATMAP_STOPS[-1][1], 255)

def draw_route_card(display : Display,
                     pal_img : Image.Image,
                     anchor : tuple[int, int],
                     size : tuple[int, int],
                     points : list[tuple],
                     padding : int = 14,
                     line_width : int = 4) -> None:

    """
    Draws a schematic line drawing of a GPS route (list of (lat, lon)
    or (lat, lon, elevation_m) tuples) on a transparent background.
    With elevation data, the line is colored as an elevation heatmap
    (blue = lowest point, red = highest); otherwise it falls back to a
    plain Strava-orange line. True RGBA colors are dithered onto the
    display's fixed e-ink palette (see to_spectra6), since none of
    them exist in SPECTRA6_COLORS.
    """

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if len(points) >= 2:
        pixel_points = _project_route_points(points, size, padding)
        elevations = [p[2] if len(p) > 2 else None for p in points]

        if all(e is not None for e in elevations) and min(elevations) < max(elevations):  # type: ignore[type-var]
            min_ele, max_ele = min(elevations), max(elevations)  # type: ignore[type-var]
            ele_range = max_ele - min_ele
            for i in range(len(pixel_points) - 1):
                t = (elevations[i] - min_ele) / ele_range
                overlay_draw.line([pixel_points[i], pixel_points[i + 1]], fill = _elevation_color(t), width = line_width, joint = "curve")
        else:
            overlay_draw.line(pixel_points, fill = STRAVA_ORANGE, width = line_width, joint = "curve")
    else:
        font = ImageFont.truetype(FONT_REGULAR_CONDENSED, size = 13)
        overlay_draw.text((size[0] / 2, size[1] / 2), "Keine GPS-Daten", fill = (0, 0, 0, 255), font = font, anchor = "mm")

    quantized = to_spectra6(overlay, pal_img)
    paste_with_transparency(display.image, quantized, anchor)

def draw_elevation_legend(display : Display,
                          pal_img : Image.Image,
                          anchor : tuple[int, int],
                          size : tuple[int, int]) -> None:

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    label_font = _select_font(11, False, True)
    line_y = size[1] / 2
    line_left = 92
    line_right = 152
    segments = 16
    segment_width = (line_right - line_left) / segments

    for i in range(segments):
        t = i / (segments - 1)
        x0 = line_left + i * segment_width
        x1 = line_left + (i + 1) * segment_width
        overlay_draw.line((x0, line_y, x1, line_y), fill = _elevation_color(t), width = 5)

    overlay_draw.text((line_right + 10, line_y), "Höhe", fill = (0, 0, 0, 255), font = label_font, anchor = "lm")
    quantized = to_spectra6(overlay, pal_img)
    paste_with_transparency(display.image, quantized, anchor)

def render_stat_block(display : Display,
                       pal_img : Image.Image,
                       anchor : tuple[int, int],
                       size : tuple[int, int],
                       entries : list[dict]) -> None:

    """
    Draws a set of text entries (each a dict with text, rel_pos, color
    (RGBA tuple), fontsize, and optionally bold/condensed/anchor) onto
    one transparent overlay, then dithers it onto the e-ink palette in
    a single pass. Lets a block mix crisp black text with colors like
    Strava orange or gray that don't exist in SPECTRA6_COLORS.
    """

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for entry in entries:
        font = _select_font(entry["fontsize"], entry.get("bold", True), entry.get("condensed", False))
        x = entry["rel_pos"][0] * size[0]
        y = entry["rel_pos"][1] * size[1]
        overlay_draw.text((x, y), entry["text"], fill = entry["color"], font = font, anchor = entry.get("anchor", "mm"))

    quantized = to_spectra6(overlay, pal_img)
    paste_with_transparency(display.image, quantized, anchor)

def draw_weekly_distance_chart(display : Display,
                               pal_img : Image.Image,
                               anchor : tuple[int, int],
                               size : tuple[int, int],
                               weekly_distances : list[dict]) -> None:

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    date_font = _select_font(10, False, True)
    km_font = _select_font(16, False, True)

    chart_left = 30
    chart_right = size[0] - 12
    chart_top = 12
    chart_bottom = size[1] - 18
    chart_height = chart_bottom - chart_top
    km_label = Image.new("RGBA", (24, 42), (0, 0, 0, 0))
    km_label_draw = ImageDraw.Draw(km_label)
    km_label_draw.text((12, 21), "KM", fill = (0, 0, 0, 255), font = km_font, anchor = "mm")
    km_label = km_label.rotate(90, expand = True)
    overlay.alpha_composite(km_label, (0, int((chart_top + chart_bottom - km_label.height) / 2)))
    max_distance = max((week.get("distance_km", 0) for week in weekly_distances), default = 0)
    max_distance = max(max_distance, 1)
    bar_gap = 5
    bar_width = (chart_right - chart_left - bar_gap * (len(weekly_distances) - 1)) / len(weekly_distances) if weekly_distances else 0

    overlay_draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill = (0, 0, 0, 255), width = 1)
    for i, week in enumerate(weekly_distances):
        distance = week.get("distance_km", 0)
        bar_x = chart_left + i * (bar_width + bar_gap)
        bar_h = chart_height * distance / max_distance
        bar_top = chart_bottom - bar_h
        overlay_draw.rectangle((bar_x, bar_top, bar_x + bar_width, chart_bottom), fill = STRAVA_ORANGE)
        overlay_draw.text((bar_x + bar_width / 2, size[1] - 7), week.get("label", ""), fill = (0, 0, 0, 255), font = date_font, anchor = "ms")

    quantized = to_spectra6(overlay, pal_img)
    paste_with_transparency(display.image, quantized, anchor)

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

    divider = GUIBox((display.size[0], 3), (0, HEADER_H - 3), WHITE)
    divider.draw_dithered(display.draw, BLACK, WHITE, dither_count = 2)

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
    last_act_name : str = recent[0].get("name", "-")
    left_label = GUIBox((left_w, LABEL_H), (MARGIN, content_y), WHITE)
    
    left_label.add_text(last_act_name, (0.5, 0.5), BLACK, fontsize = 20, bold = True, anchor = "mm")

    left_label.draw_box(display.draw)



    rows_y = content_y + LABEL_H + GAP // 2
    rows_h = content_h - LABEL_H - GAP // 2

    # INFO-BOX MIT DEN KENNZAHLEN DER LETZTEN AKTIVITÄT (GESCHWINDIGKEIT, HÖHENMETER, DISTANZ)
    INFO_BOX_H = 48
    info_box = GUIBox((left_w, INFO_BOX_H), (MARGIN, rows_y), WHITE)
    info_box.draw_box(display.draw)

    last_act = recent[0] if recent else {}
    avg_speed = last_act.get("average_speed_kmh")
    stat_chips = [
        ("speed.jpg", f"{avg_speed:.1f} km/h" if avg_speed is not None else "-"),
        ("ascent_icon.jpg", f"{last_act.get('elevation_gain_m', 0)} m"),
        ("distance_icon.jpeg", f"{last_act.get('distance_km', 0):.1f} km"),
    ]

    icon_h = 30
    col_w = left_w / len(stat_chips)

    for i, (icon_filename, value_text) in enumerate(stat_chips):
        icon = load_icon(pal_img, icon_filename)
        col_x = MARGIN + i * col_w
        icon_anchor = (col_x, rows_y + (INFO_BOX_H - icon_h) / 2)
        draw_icon_value(display, icon, icon_anchor, icon_h, value_text, BLACK, fontsize = 18, center_in_width = col_w)

    route_y = rows_y + INFO_BOX_H + GAP
    legend_h = 26
    legend_gap = 4
    power_box_h = 48
    route_h = rows_h - INFO_BOX_H - GAP - legend_h - legend_gap - GAP - power_box_h
    route_points = data.get("last_activity_route") or []
    draw_route_card(display, pal_img, (MARGIN, route_y), (left_w, route_h), route_points, padding = 14)
    draw_elevation_legend(display, pal_img, (MARGIN, route_y + route_h + legend_gap), (left_w, legend_h))

    power_box_y = route_y + route_h + legend_gap + legend_h + GAP
    power_metrics = data.get("power_metrics") or {}
    power_chips = [
        ("Average_P.jpg", power_metrics.get("average_power")),
        ("NP.jpg", power_metrics.get("normalized_power")),
        ("Power_3S.jpg", power_metrics.get("top_power_3s")),
    ]
    power_col_w = left_w / len(power_chips)
    for i, (icon_filename, value) in enumerate(power_chips):
        icon = load_icon(pal_img, icon_filename)
        col_x = MARGIN + i * power_col_w
        icon_anchor = (col_x, power_box_y + (power_box_h - icon_h) / 2)
        value_text = str(int(value)) if value is not None else "-"
        draw_icon_value(display, icon, icon_anchor, icon_h, value_text, BLACK, fontsize = 18, center_in_width = power_col_w)

    # RIGHT COLUMN: YEAR-TO-DATE STATS
    ytd = data.get("ytd") or {}
    ytd_distance_km = ytd.get("distance_km", 0)
    ytd_elevation_m = ytd.get("elevation_gain_m", 0)
    earth_pct = ytd_distance_km / EARTH_CIRCUMFERENCE_KM * 100
    everest_x = ytd_elevation_m / EVEREST_HEIGHT_M

    right_label = GUIBox((right_w, LABEL_H), (right_x, content_y), WHITE)
    right_label.add_text("DIESES JAHR", (0.5, 0.5), BLACK, fontsize = 20, bold = True, anchor = "mm")
    right_label.draw_box(display.draw)

    N_BLOCKS = 3
    DIVIDER_GAP = 8
    DIVIDER_THICKNESS = 3
    divider_center_x = right_x + right_w / 2
    divider_w = int(right_w * 0.9)

    stat_area_y = content_y + LABEL_H + 6
    stat_area_h = content_h - LABEL_H - 6
    dividers_h = (N_BLOCKS - 1) * (2 * DIVIDER_GAP + DIVIDER_THICKNESS)
    block_h = int((stat_area_h - dividers_h) / N_BLOCKS)

    y = stat_area_y

    render_stat_block(display, pal_img, (right_x, y), (right_w, block_h), [
        {"text": "GESAMTDISTANZ", "rel_pos": (0.5, 0.18), "color": (0, 0, 0, 255), "fontsize": 16, "bold": False},
        {"text": f"{ytd_distance_km:.1f} km", "rel_pos": (0.5, 0.54), "color": STRAVA_ORANGE, "fontsize": 26},
        {"text": f"{earth_pct:.2f}% der Erdumrundung", "rel_pos": (0.5, 0.84), "color": (0, 0, 0, 255), "fontsize": 14, "bold": False, "condensed": True},
    ])
    y += block_h

    y += DIVIDER_GAP
    draw_light_divider(display, divider_center_x, y, divider_w)
    y += DIVIDER_GAP + DIVIDER_THICKNESS

    render_stat_block(display, pal_img, (right_x, y), (right_w, block_h), [
        {"text": "HÖHENMETER", "rel_pos": (0.5, 0.18), "color": (0, 0, 0, 255), "fontsize": 16, "bold": False},
        {"text": f"{ytd_elevation_m:.0f} m", "rel_pos": (0.5, 0.54), "color": STRAVA_ORANGE, "fontsize": 26},
        {"text": f"{everest_x:.1f}× Mount Everest", "rel_pos": (0.5, 0.84), "color": (0, 0, 0, 255), "fontsize": 14, "bold": False, "condensed": True},
    ])
    y += block_h

    y += DIVIDER_GAP
    draw_light_divider(display, divider_center_x, y, divider_w)
    y += DIVIDER_GAP + DIVIDER_THICKNESS

    draw_weekly_distance_chart(display, pal_img, (right_x, y), (right_w, block_h), data.get("weekly_cycling_distance") or [])

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