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
    r, g, b, a = img.split()
    a = a.point(lambda v: 0 if v < 20 else 255)

    return Image.merge("RGBA", (r, g, b, a))

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

def draw_vertical_divider(display : Display, x : int, center_y : float, height : int, thickness : int = 2, color : int = BLACK) -> None:

    """
    Draws a solid vertical divider line of the given height, centered on
    center_y.
    """

    display.draw.line((x, center_y - height / 2, x, center_y + height / 2), fill = color, width = thickness)

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

def draw_weather_icon(display : Display, anchor : tuple[int, int], state : str, size : int = 22) -> None:

    draw = display.draw
    x, y = anchor
    center_x = x + size // 2
    center_y = y + size // 2
    if state == "clear":
        draw.ellipse((x + 8, y + 8, x + size - 8, y + size - 8), outline = STRAVA_ORANGE, width = 2)
        ray_start = 3
        ray_end = 6
        for start, end in (
            ((center_x, y + ray_start), (center_x, y + ray_end)),
            ((center_x, y + size - ray_start), (center_x, y + size - ray_end)),
            ((x + ray_start, center_y), (x + ray_end, center_y)),
            ((x + size - ray_start, center_y), (x + size - ray_end, center_y)),
            ((x + 6, y + 6), (x + 8, y + 8)),
            ((x + size - 6, y + 6), (x + size - 8, y + 8)),
            ((x + 6, y + size - 6), (x + 8, y + size - 8)),
            ((x + size - 6, y + size - 6), (x + size - 8, y + size - 8)),
        ):
            draw.line((*start, *end), fill = STRAVA_ORANGE, width = 1)
    else:
        draw.ellipse((x + 2, y + 8, x + 14, y + 18), fill = BLACK)
        draw.ellipse((x + 8, y + 4, x + 19, y + 18), fill = BLACK)
        draw.rectangle((x + 7, y + 12, x + 21, y + 18), fill = BLACK)
        if state == "rain":
            draw.line((x + 8, y + 21, x + 6, y + size), fill = BLUE, width = 2)
            draw.line((x + 15, y + 21, x + 13, y + size), fill = BLUE, width = 2)
        elif state == "showers":
            draw.line((x + 11, y + 21, x + 9, y + size), fill = BLUE, width = 2)

def draw_wind_arrow(display : Display, anchor : tuple[int, int], degrees : float, size : int = 18, color : int = BLACK) -> None:

    """
    Draws a bold arrow (thick shaft + filled triangular head) centered in
    a size x size box, pointing in the direction the wind is blowing
    towards (degrees is the meteorological "coming from" bearing
    Open-Meteo reports, 0=North/up, clockwise - so the arrow points the
    opposite way, degrees + 180).
    """

    draw = display.draw
    cx = anchor[0] + size / 2
    cy = anchor[1] + size / 2
    angle = math.radians((degrees + 180) % 360)

    def _offset(base : tuple[float, float], bearing_rad : float, length : float) -> tuple[float, float]:
        return (base[0] + length * math.sin(bearing_rad), base[1] - length * math.cos(bearing_rad))

    half_len = size * 0.46
    head_len = size * 0.4
    head_half_width = size * 0.24

    tip = _offset((cx, cy), angle, half_len)
    tail = _offset((cx, cy), angle, -half_len)
    head_base = _offset((cx, cy), angle, half_len - head_len)
    side1 = _offset(head_base, angle + math.pi / 2, head_half_width)
    side2 = _offset(head_base, angle - math.pi / 2, head_half_width)

    draw.line([tail, head_base], fill = color, width = 3)
    draw.polygon([tip, side1, side2], fill = color)

def _haversine_km(p1 : tuple, p2 : tuple) -> float:

    """
    Great-circle distance in km between two (lat, lon, ...) points.
    """

    EARTH_RADIUS_KM = 6371
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2

    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))

STRAVA_ORANGE = (252, 76, 2, 255)

def _project_route_points(points : list[tuple],
                           box_size : tuple[int, int],
                           padding : int = 10) -> list[tuple[float, float]]:

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

    return [
        (
            offset_x + (p[1] - min_lon) * math.cos(lat_mid_rad) * scale,
            offset_y + (max_lat - p[0]) * scale,  # BILD-Y WÄCHST NACH UNTEN, BREITENGRAD NACH OBEN
        )
        for p in points
    ]

def draw_route_map(display : Display,
                    pal_img : Image.Image,
                    anchor : tuple[int, int],
                    size : tuple[int, int],
                    points : list[tuple],
                    padding : int = 10,
                    line_width : int = 4) -> None:

    """
    Draws a schematic birds-eye line drawing of a GPS route (list of
    (lat, lon, ...) tuples) on a transparent background - no map/terrain
    underlay, plain Strava-orange line.
    """

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if len(points) >= 2:
        pixel_points = _project_route_points(points, size, padding)
        overlay_draw.line(pixel_points, fill = STRAVA_ORANGE, width = line_width, joint = "curve")
    else:
        font = ImageFont.truetype(FONT_REGULAR_CONDENSED, size = 13)
        overlay_draw.text((size[0] / 2, size[1] / 2), "Keine GPS-Daten", fill = (0, 0, 0, 255), font = font, anchor = "mm")

    quantized = to_spectra6(overlay, pal_img)
    paste_with_transparency(display.image, quantized, anchor)

CLIMB_MIN_LENGTH_M = 750.0

def _classify_climbs(distances_km : list[float],
                      elevations : list[float],
                      min_length_m : float = CLIMB_MIN_LENGTH_M,
                      smoothing_window : int = 5,
                      pullback_tolerance_m : float = 5.0) -> list[bool]:

    """
    Marks each point as belonging to a sustained climb (True) or not
    (False). Elevation is first smoothed with a small moving average to
    ignore GPS noise. A climb run tracks its running peak and only ends
    once elevation has pulled back more than pullback_tolerance_m below
    that peak (so small dips within a climb don't end it, but an actual
    descent does - unlike a naive step-to-step tolerance, which never
    breaks on a long, gradual descent where every single step is small).
    A finished run only counts as a climb if it covers at least
    min_length_m of route distance and nets an elevation gain.
    """

    n = len(elevations)
    if n < 2:
        return [False] * n

    half = smoothing_window // 2
    smoothed = [
        sum(elevations[max(0, i - half):min(n, i + half + 1)]) / len(elevations[max(0, i - half):min(n, i + half + 1)])
        for i in range(n)
    ]

    is_climb = [False] * n
    run_start = 0
    run_peak_i = 0

    def close_run(end_i : int) -> None:
        run_distance_m = (distances_km[end_i] - distances_km[run_start]) * 1000
        if run_distance_m >= min_length_m and smoothed[end_i] > smoothed[run_start]:
            for j in range(run_start, end_i + 1):
                is_climb[j] = True

    for i in range(1, n):
        if smoothed[i] > smoothed[run_peak_i]:
            run_peak_i = i
        elif smoothed[run_peak_i] - smoothed[i] > pullback_tolerance_m:
            close_run(run_peak_i)
            run_start = i
            run_peak_i = i

    close_run(run_peak_i)
    return is_climb

def draw_elevation_profile(display : Display,
                            pal_img : Image.Image,
                            anchor : tuple[int, int],
                            size : tuple[int, int],
                            points : list[tuple]) -> None:

    """
    Draws a distance/elevation profile of a route (list of (lat, lon,
    elevation_m) tuples) as a line chart: x = cumulative distance, y =
    elevation. Only segments that are part of a sustained climb (see
    _classify_climbs, CLIMB_MIN_LENGTH_M) get a solid Strava-orange fill;
    flat/rolling/descending stretches stay unfilled so minor bumps don't
    turn the whole profile into visual noise. Falls back to a placeholder
    text if fewer than 2 points carry elevation.
    """

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    valid_points = [p for p in points if len(p) > 2 and p[2] is not None]

    if len(valid_points) < 2:
        font = ImageFont.truetype(FONT_REGULAR_CONDENSED, size = 13)
        overlay_draw.text((size[0] / 2, size[1] / 2), "Keine Höhendaten", fill = (0, 0, 0, 255), font = font, anchor = "mm")
        quantized = to_spectra6(overlay, pal_img)
        paste_with_transparency(display.image, quantized, anchor)
        return

    distances_km = [0.0]
    for i in range(1, len(valid_points)):
        distances_km.append(distances_km[-1] + _haversine_km(valid_points[i - 1], valid_points[i]))
    total_distance_km = distances_km[-1] or 1e-9

    elevations = [p[2] for p in valid_points]
    min_ele, max_ele = min(elevations), max(elevations)
    ele_range = (max_ele - min_ele) or 1.0

    label_font = _select_font(11, False, True)
    max_ele_text = f"{max_ele:.0f} m"
    min_ele_text = f"{min_ele:.0f} m"
    ele_label_w = max(label_font.getlength(max_ele_text), label_font.getlength(min_ele_text))
    chart_left = int(ele_label_w) + 10
    chart_right = size[0] - 8
    chart_top = 16
    chart_bottom = size[1] - 6
    chart_w = chart_right - chart_left
    chart_h = chart_bottom - chart_top

    pixel_points = [
        (
            chart_left + (distances_km[i] / total_distance_km) * chart_w,
            chart_bottom - ((elevations[i] - min_ele) / ele_range) * chart_h,
        )
        for i in range(len(valid_points))
    ]

    # NUR ANSTIEGE AB CLIMB_MIN_LENGTH_M BEKOMMEN EINE FLÄCHE, DER REST BLEIBT UNGEFÜLLT
    is_climb = _classify_climbs(distances_km, elevations)
    for i in range(len(pixel_points) - 1):
        if not (is_climb[i] and is_climb[i + 1]):
            continue
        x0, y0 = pixel_points[i]
        x1, y1 = pixel_points[i + 1]
        overlay_draw.polygon([(x0, chart_bottom), (x0, y0), (x1, y1), (x1, chart_bottom)], fill = STRAVA_ORANGE)

    overlay_draw.line(pixel_points, fill = (0, 0, 0, 255), width = 2, joint = "curve")
    overlay_draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill = (0, 0, 0, 255), width = 1)

    overlay_draw.text((chart_left - 4, chart_top), max_ele_text, fill = (0, 0, 0, 255), font = label_font, anchor = "rt")
    overlay_draw.text((chart_left - 4, chart_bottom), min_ele_text, fill = (0, 0, 0, 255), font = label_font, anchor = "rs")

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

    if not weekly_distances:
        placeholder_font = _select_font(13, False, True)
        overlay_draw.text((size[0] / 2, size[1] / 2), "Keine Wochendaten", fill = (0, 0, 0, 255), font = placeholder_font, anchor = "mm")
        quantized = to_spectra6(overlay, pal_img)
        paste_with_transparency(display.image, quantized, anchor)
        return

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
        overlay_draw.text((bar_x + bar_width / 2, bar_top - 4), f"{distance:.1f}", fill = (0, 0, 0, 255), font = date_font, anchor = "ms")
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

    weather = data.get("weather") or {}
    if weather:
        # DREI BEREICHE VON RECHTS: PROGNOSE-ICON | WIND (PFEIL + KM/H) | TEMPERATUR.
        # LAYOUT WIRD ANHAND DER TATSÄCHLICHEN INHALTSBREITEN VON RECHTS NACH LINKS
        # AUFGEBAUT, DAMIT JEDE TRENNLINIE LINKS/RECHTS GENAU DASSELBE PADDING HAT
        # (STATT FESTER SPALTENBREITEN, DIE JE NACH INHALT UNTERSCHIEDLICH VIEL
        # LEERRAUM UM DIE LINIE LASSEN).
        DIVIDER_PADDING = 10
        weather_icon_size = 30
        wind_arrow_size = 18

        temp_font = _select_font(18, True, True)
        wind_font = _select_font(14, True, True)

        icon_x1 = display.size[0] - MARGIN
        icon_x0 = icon_x1 - weather_icon_size
        draw_weather_icon(display, (int(icon_x0), int((HEADER_H - weather_icon_size) / 2)), weather.get("precipitation_state", "clear"), size = weather_icon_size)

        wind_text = f"{weather.get('wind_speed', '-')} km/h"
        wind_text_w = wind_font.getlength(wind_text)
        wind_gap = 5
        wind_direction_deg = weather.get("wind_direction_deg")
        wind_content_w = (wind_arrow_size + wind_gap if wind_direction_deg is not None else 0) + wind_text_w

        divider2_x = icon_x0 - DIVIDER_PADDING
        wind_x1 = divider2_x - DIVIDER_PADDING
        wind_x0 = wind_x1 - wind_content_w
        if wind_direction_deg is not None:
            draw_wind_arrow(display, (wind_x0, HEADER_H / 2 - wind_arrow_size / 2), wind_direction_deg, size = wind_arrow_size)
            display.draw.text((wind_x0 + wind_arrow_size + wind_gap, HEADER_H / 2), wind_text, fill = BLACK, font = wind_font, anchor = "lm")
        else:
            display.draw.text((wind_x0, HEADER_H / 2), wind_text, fill = BLACK, font = wind_font, anchor = "lm")

        divider1_x = wind_x0 - DIVIDER_PADDING
        temp_x1 = divider1_x - DIVIDER_PADDING
        display.draw.text((temp_x1, HEADER_H / 2), f"{weather.get('temperature', '-')}°C", fill = BLACK, font = temp_font, anchor = "rm")

        # TRENNLINIEN SO HOCH WIE DIE (GRÖSSTE) SCHRIFT DER SPALTEN
        ascent, descent = temp_font.getmetrics()
        divider_h = ascent + descent
        draw_vertical_divider(display, int(divider1_x), HEADER_H / 2, divider_h)
        draw_vertical_divider(display, int(divider2_x), HEADER_H / 2, divider_h)

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
    last_act_name : str = recent[0].get("name", "-") if recent else "Keine Aktivität"
    left_label = GUIBox((left_w, LABEL_H), (MARGIN, content_y), WHITE)

    left_label.add_text(last_act_name, (0.5, 0.5), BLACK, fontsize = 20, bold = True, anchor = "mm")

    left_label.draw_box(display.draw)
    if recent:
        kudos_icon = load_icon(pal_img, "Kudos.bmp")
        kudos = recent[0].get("kudos_count", 0)
        draw_icon_value(display, kudos_icon, (MARGIN + left_w - 62, content_y), 22, str(int(kudos)), BLACK, fontsize = 14)



    rows_y = content_y + LABEL_H + GAP // 2
    rows_h = content_h - LABEL_H - GAP // 2

    # INFO-BOX MIT DEN KENNZAHLEN DER LETZTEN AKTIVITÄT (GESCHWINDIGKEIT, HÖHENMETER, DISTANZ)
    INFO_BOX_H = 40
    info_box = GUIBox((left_w, INFO_BOX_H), (MARGIN, rows_y), WHITE)
    info_box.draw_box(display.draw)

    last_act = recent[0] if recent else {}
    avg_speed = last_act.get("average_speed_kmh")
    if recent:
        stat_chips = [
            ("speed.jpg", f"{avg_speed:.1f} km/h" if avg_speed is not None else "-"),
            ("ascent_icon.jpg", f"{last_act.get('elevation_gain_m', 0)} m"),
            ("distance_icon.jpeg", f"{last_act.get('distance_km', 0):.1f} km"),
        ]
    else:
        stat_chips = [
            ("speed.jpg", "-"),
            ("ascent_icon.jpg", "-"),
            ("distance_icon.jpeg", "-"),
        ]

    icon_h = 34
    col_w = left_w / len(stat_chips)

    for i, (icon_filename, value_text) in enumerate(stat_chips):
        icon = load_icon(pal_img, icon_filename)
        col_x = MARGIN + i * col_w
        icon_anchor = (col_x, rows_y + (INFO_BOX_H - icon_h) / 2)
        draw_icon_value(display, icon, icon_anchor, icon_h, value_text, BLACK, fontsize = 18, center_in_width = col_w)

    # POWER-CHIPS DIREKT UNTER DEN ANDEREN DREI KENNZAHLEN
    row_gap = 6
    chip_gap = 0
    power_box_h = 40
    power_box_y = rows_y + INFO_BOX_H + chip_gap
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

    # ROUTEN-KARTE MIT HÖHENPROFIL DARUNTER - HÖHENPROFIL BLEIBT FIX, DIE
    # ROUTEN-KARTE BEKOMMT DEN GESAMTEN DURCH DIE ENGEREN CHIPS GEWONNENEN PLATZ
    maps_y = power_box_y + power_box_h + row_gap
    maps_h = rows_h - INFO_BOX_H - power_box_h - chip_gap - 2 * row_gap
    ELEVATION_PROFILE_H = 69
    elevation_h = ELEVATION_PROFILE_H
    route_map_h = maps_h - elevation_h - row_gap

    route_points = data.get("last_activity_route") or []
    draw_route_map(display, pal_img, (MARGIN, maps_y), (left_w, route_map_h), route_points)

    elevation_y = maps_y + route_map_h + row_gap
    draw_elevation_profile(display, pal_img, (MARGIN, elevation_y), (left_w, elevation_h), route_points)

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

    # VERSIONS-LABEL UNTEN LINKS, IM RAND UNTER DEM INHALTSBEREICH
    release_label = data.get("release_label") or "v?.?.?"
    release_font = _select_font(10, False, True)
    max_label_w = display.size[0] - 2 * MARGIN
    while release_font.getlength(release_label) > max_label_w and len(release_label) > 1:
        release_label = release_label[:-2] + "…"
    display.draw.text((MARGIN, display.size[1] - MARGIN / 2), release_label, fill = BLACK, font = release_font, anchor = "lm")

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