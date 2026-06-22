from PIL import Image, ImageDraw, ImageFont
from matplotlib import pyplot as plt
from datetime import datetime

# Measurements for the display

width = 600
height = 400


margin_factor = 0.05
w_margin = margin_factor * width
h_margin = margin_factor * width

# INITIALIZE IMAGE

image = Image.new('RGB', (width, height),color = (255,255,255)) 
draw = ImageDraw.Draw(image)

# LOAD FONTS 

font_regular = ImageFont.truetype("display/fonts/RobotoCondensed-Regular.ttf", 14)
font_regular_large = ImageFont.truetype("display/fonts/RobotoCondensed-Regular.ttf", 20)
font_bold = ImageFont.truetype("display/fonts/RobotoCondensed-Bold.ttf", 14)
font_bold_large = ImageFont.truetype("display/fonts/RobotoCondensed-Bold.ttf", 20)



#LOAD LOGOS

strava_logo_white = Image.open("display/img/strava-logo-full-white.png")
strava_logo_orange = Image.open("display/img/strava-logo-full-orange.png").resize((84,20), Image.Resampling.LANCZOS)


name = "Johannes Schönau"
font = ImageFont.load_default()

anchor_name : tuple = (w_margin, h_margin)
anchor_date : tuple = (0.8 * width, h_margin)
anchor_rides_table : tuple = (w_margin, anchor_name[1] + 40)


if 6 <= datetime.now().hour < 11:

    greeting : str = "Guten Morgen"

elif 11 <= datetime.now().hour < 18:

    greeting : str = "Guten Tag"

elif 18 <= datetime.now().hour < 22:

    greeting : str = "Guten Abend"

elif 22 <= datetime.now().hour < 6:

    greeting : str = "Gute Nacht"

else:
    greeting : str = "Hallo"

draw_name = draw.text(anchor_name, str(greeting + ", " + name + "!"), font = font_bold, fill = (0,0,0))


date_string : str =str(datetime.now().day) + "." + str(datetime.now().month) + "." + str(datetime.now().year)
draw_date = draw.text(anchor_date, date_string, font = font_regular, fill = (0,0,0))

bbox_rides_table = draw.rectangle((anchor_rides_table, (width/2 ,height - h_margin)),
                                   fill = None, outline = (200,200,200))

ride_1 = draw.text(anchor_rides_table, "Afternoon Ride         220W        14.3 km", fill = "black", font = font_regular)


bbox_display = draw.rectangle(xy = ((0,0),(width,height)),fill = None, outline = (0,255,0), width = 3)

image.paste(strava_logo_orange, (50,50), strava_logo_orange)

image.show()