import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib import pyplot as plt
from datetime import datetime

width = 800
height = 480

margin_factor = 0.05
w_margin = margin_factor * width
h_margin = margin_factor * width

image = Image.new('RGB', (width, height),color = (255,255,255))
draw = ImageDraw.Draw(image)

name = "Johannes Schoenau"
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

draw_name = draw.text(anchor_name, str(greeting + ", " + name + "!"), font_size = 20, fill = (0,0,0))


date_string : str =str(datetime.now().day) + "." + str(datetime.now().month) + "." + str(datetime.now().year)
draw_date = draw.text(anchor_date, date_string, font_size = 20, fill = (0,0,0))

bbox_rides_table = draw.rectangle((anchor_rides_table, (width/2 ,height - h_margin)),
                                   fill = None, outline = (200,200,200))

ride_1 = draw.text(anchor_rides_table, "Afternoon Ride         220W        14.3 km", fill = "black")


bbox_display = draw.rectangle(xy = ((0,0),(width,height)),fill = None, outline = (0,255,0), width = 3)

array = np.array(image)

plt.imshow(array)
plt.axis("off")
plt.show()  