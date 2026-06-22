from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import locale

class GUIBox:

    """
    Rectangle with a given size (width, height).
    Anchor position at the top left (x,y).
    Background and textcolors are given as (R,G,B)
    """

    def __init__(self, size : tuple[float,float],
                 anchor : tuple[float,float],
                 backgroud_RBG : tuple[int,...]):
                #  outline_RGB : tuple[int,...],
               
        
        self.size = size
        self.anchor = anchor
        self.backgroud_RGB = backgroud_RBG
        self.text_list = []
        # self.outline_RGB = outline_RGB


    def add_text(self,
                 text : str,
                 rel_anchor : tuple[float, float],
                 text_color : tuple[int,...],
                 fontsize : int,
                 bold : bool = False) -> None: 
    
        self.text_list.append({
            "text" : text,
            "rel_anchor" : rel_anchor,
            "fontsize" : fontsize,
            "bold" : bold,
            "text_color" : text_color
        })

    def draw(self, draw : ImageDraw.ImageDraw) -> None:

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

                font = ImageFont.truetype("display/fonts/Roboto-Bold.ttf", size = item["fontsize"])

            else:

                font = ImageFont.truetype("display/fonts/Roboto-Regular.ttf", size = item["fontsize"])

            x1 = self.anchor[0] + item["rel_anchor"][0] * self.size[0]
            y1 = self.anchor[1] + item["rel_anchor"][1] * self.size[1]

            draw.text((x1,y1), item["text"], item["text_color"], font = font)    
    
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

locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")

# DISPLAY DIMENSIONS
width = 600
height = 400

# INITIALIZE IMAGE
image = Image.new('RGB', (width, height),color = (255,255,255)) 
draw = ImageDraw.Draw(image)

#LOAD LOGOS
strava_logo_white = Image.open("display/img/strava-logo-full-white.png")
strava_logo_orange = Image.open("display/img/strava-logo-full-orange.png").resize((84,20), Image.Resampling.LANCZOS)

# image.paste(strava_logo_orange, (50,50), strava_logo_orange)

title_box = GUIBox(size = (580,30), 
             anchor = (10,10),
             backgroud_RBG = (int(0.035 * 255), int(0.121 * 255), int(0.246 * 255)))


title_string = generate_greeting() + ", " + "johannes schoenau!"
title_box.add_text(title_string, rel_anchor = (0.02, 0.12), text_color = (255,255,255),fontsize = 20, bold = True)
datestring = datetime.now().strftime("%A, %d.%m.%y")
title_box.add_text(datestring, rel_anchor = (0.73, 0.2), text_color = (200,200,200), fontsize = 17)

title_box.draw(draw = draw)

title_box_rides = GUIBox(size = (320,30),
                         anchor = (10, 50),
                         backgroud_RBG = (180,180,180))
title_box_rides.draw(draw = draw)

image.show()