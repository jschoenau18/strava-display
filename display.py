import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib import pyplot as plt
width = 800
height = 480

image = Image.new('RGB', (width, height), (255,255,255))
draw = ImageDraw.Draw(image)
name = "Johannes Schoenau"
font = ImageFont.load_default()

draw.text((10,10), name, font_size = 70, fill = (0,0,0))
draw.text((10,70), "Strava API", font_size = 70, fill = "red")


array = np.array(image)

plt.imshow(array)
plt.axis("off")
plt.show()  