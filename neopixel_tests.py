from neopixel import NeoPixel
from machine import Pin

numpix = 30
pixels = NeoPixel(Pin(28), 24)

yellow = (255, 100, 0)
orange = (255, 50, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
red = (255, 0, 0)
black = (0, 0, 0)
color0 = red

pixels.fill(black)
pixels.write()