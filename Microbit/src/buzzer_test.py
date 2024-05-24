from microbit import button_a, pin1, pin0, pin2 #type: ignore
from neopixel import NeoPixel
import time

class Color:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    RED = (255, 0, 0)
    GREEN = (0, 225, 0)
    BLUE = (0, 0, 255)

class BuzzerTest:
    def __init__(self, buttonPin, neopixelPin, pixelCount):
        self.__active = False

        self.__buttonPin = buttonPin

        self.__pixelCount = pixelCount
        self.__pixels = NeoPixel(neopixelPin, pixelCount)
        
        pin2.write_digital(1)

        self.updatePixels()

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
            if button_a.is_pressed() or self.__buttonPin.read_digital():
                self.__active = not self.__active
                self.updatePixels()
                time.sleep(1)

buzzerTest = BuzzerTest(pin1, pin0, 7)
buzzerTest.mainloop()
