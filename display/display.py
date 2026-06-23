from PIL import Image, ImageDraw, ImageFont, ImagePalette
from datetime import datetime
import locale


# ENTHÄLT ZB GRÖßE, FARBEN FONTS
class Display:
    
    def __init__(self, size : tuple[int,int], colors : list[int]):
        
        self.size = size
        self.colors = colors
        self.title_box : GUIBox
        self.title_box_rides : GUIBox
        self.ride_box : GUIBox
        
        self.image : Image.Image = Image.new('P', self.size, color = 1) #fixed color palette for e ink, white backgroud
        self.draw = ImageDraw.Draw(self.image, mode = 'P')
        self.image.putpalette(self.colors)

class GUIBox:

    """
    Rectangle with a given size (width, height).
    Anchor position at the top left (x,y).
    Background and textcolors are given as (R,G,B)
    """

    def __init__(self, size : tuple[int,int],
                 anchor : tuple[int,int],
                 backgroud_color : int):
                #  outline_RGB : tuple[int,...],
               
        """
        Backgroud color has to be selectod from the color palette of the parent display 
        """
        self.size = size
        self.anchor = anchor
        self.backgroud_RGB = backgroud_color
        self.text_list = []
        # self.outline_RGB = outline_RGB


    def add_text(self,
                 text : str,
                 rel_anchor : tuple[float, float],
                 text_color : int,
                 fontsize : int,
                 bold : bool = False,
                 condensed : bool = False) -> None: 
    
        self.text_list.append({
            "text" : text,
            "rel_anchor" : rel_anchor,
            "fontsize" : fontsize,
            "bold" : bold,
            "condensed" : condensed, 
            "text_color" : text_color
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

        draw.rectangle((x1, y1, x2, y2), self.backgroud_RGB, outline = None, width = 10)

        # DRAW ALL THE TEXT ENTRIES

        
        for item in self.text_list:
            
            if item["bold"]:
                if item["condensed"]:

                    font = ImageFont.truetype(font_bold_con, size = item["fontsize"])

                else:

                    font = ImageFont.truetype(font_bold, size = item["fontsize"])
            else:
                if item["condensed"]:

                    font = ImageFont.truetype(font_regular_con, size = item["fontsize"])

                else: 

                    font = ImageFont.truetype(font_regular, size = item["fontsize"])

            x1 = self.anchor[0] + item["rel_anchor"][0] * self.size[0]
            y1 = self.anchor[1] + item["rel_anchor"][1] * self.size[1]

            draw.text(xy = (x1,y1), text = item["text"], fill = item["text_color"], font = font)    

# FUNKTION, DIE AUS DER MAIN AUFGERUFEN WIRD
# BRAUCHT DIE API DATEN

def make_gui() -> Image.Image:
    ...

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

# SET TO GERMAN TIME FORMAT
locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")

#LOAD LOGOS
strava_logo_white = Image.open("display/img/strava-logo-full-white.png")
strava_logo_orange = Image.open("display/img/strava-logo-full-orange.png").resize((84,20), Image.Resampling.LANCZOS)

#LOAD FONTS
font_regular : str = "display/fonts/Roboto-Regular.ttf"
font_regular_con : str = "display/fonts/RobotoCondensed-Regular.ttf"
font_bold : str = "display/fonts/Roboto-Bold.ttf"
font_bold_con : str = "display/fonts/RobotoCondensed-Bold.ttf"

# image.paste(strava_logo_orange, (50,50), strava_logo_orange)

spectra6_colors = [
    0,   0,   0,      # 0: Schwarz
    255, 255, 255,    # 1: Weiß
    255, 0,   0,      # 2: Rot
    255, 255, 0,      # 3: Gelb
    0,   0,   255,    # 4: Blau
    0,   255, 0       # 5: Grün
]

# FILL THE LIST REST OF THE WIsTH ZEROS
spectra6_colors = spectra6_colors + [0] * (768 - len(spectra6_colors))

# https://www.alibaba.com/product-detail/Sunlight-readable-4-inch-400-600_1601808118902.html?spm=a2700.prosearch.normal_offer.d_image.7c5467afJgX2JB&priceId=ceca9c4c4572456596046ef68faf56f6
test_display : Display = Display((600,400), spectra6_colors)


test_display.title_box = GUIBox((580,30), (10,10), backgroud_color = 3)
test_display.title_box.add_text("Test", (0.1,0.1), text_color = 4, fontsize = 30, bold = True)
test_display.title_box.draw_box(draw = test_display.draw)

dithered_display = Display((600,400), spectra6_colors)

dithered_display.title_box = GUIBox((580,30), (10,10), backgroud_color = 3)
dithered_display.title_box.draw_dithered(dithered_display.draw, 3, 2, 2)
dithered_display.image.show()