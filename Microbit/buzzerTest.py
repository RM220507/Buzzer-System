from microbit import button_a, pin1 #type: ignore
from neopixel import NeoPixel
import time

class Color:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    
    RED = (255, 0, 0)
    GREEN = (0, 225, 0)
    BLUE = (0, 0, 255)
    
class BuzzerTest:
    def __init__(self, neopixelPin, pixelCount):
        self.__active = False
        
        self.__pixelCount = pixelCount
        self.__pixels = NeoPixel(neopixelPin, pixelCount, bpp=3)
        
    def updatePixels(self):
        if self.__active:
            color = Color.GREEN
        else:
            color = Color.RED
        
        for i in range(self.__pixelCount):
            self.__pixels[i] = color
        self.__pixels.show() # type: ignore
        
    def mainloop(self):
        while True:
            if button_a.is_pressed():
                self.__active = not self.__active
                self.updatePixels()
                time.sleep(1)
                
buzzerTest = BuzzerTest(pin1, 1)
buzzerTest.mainloop()