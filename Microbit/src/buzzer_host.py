import radio #type: ignore
from microbit import button_a, pin1, pin0 #type: ignore
from neopixel import NeoPixel
from time import sleep_ms

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)

class ColorProfile:
    def __init__(self, inactiveColor, waitingColor, activeColor, lockedColor):
        self.__inactiveColor = inactiveColor
        self.__waitingColor = waitingColor
        self.__activeColor = activeColor
        self.__lockedColor = lockedColor

    def get(self, state):
        if state == "inactive":
            return self.__inactiveColor
        elif state == "waiting":
            return self.__waitingColor
        elif state == "active":
            return self.__activeColor
        elif state == "locked":
            return self.__lockedColor
        else:
            return (0, 0, 0)

DEFAULT_COLOR_PROFILE = ColorProfile(GREEN, BLUE, PURPLE, BLACK) # default color palette is all off, so the neopixels aren't on before the buzzer is properly initialised

class HostBuzzer:
    def __init__(self, buttonPin, neopixelPin, pixelCount):
        # setup the radio module
        radio.config(group=16, power=7)
        radio.on()

        self.__buttonPin = buttonPin

        self.__displayPixels = True
        self.__pixelCount = pixelCount
        self.__pixels = NeoPixel(neopixelPin, pixelCount)
        self.displayColor(GREEN)

        self.__ID = 255 # get the ID before continuing with initialisation

        self.__state = "inactive"

        self.__colorProfile = DEFAULT_COLOR_PROFILE

    def open(self):
        self.__state = "waiting"
        self.updatePixels()

    def close(self):
        self.__state = "inactive"
        self.updatePixels()

    def updatePixels(self):
        # get the correct color from ColorProfile object, and make the neopixels display it
        if self.__displayPixels:
            color = self.__colorProfile.get(self.__state)
            self.displayColor(color)
        else:
            self.displayColor(BLACK)

    def displayColor(self, color):
        for i in range(self.__pixelCount):
            self.__pixels[i] = color
        self.__pixels.show() # type: ignore

    def toggleLight(self, state=None):
        if state is not None:
            self.__displayPixels = state
        else:
            self.__displayPixels = not self.__displayPixels

        self.updatePixels()

    def setActive(self):
        self.__state = "active"
        self.updatePixels()

    def mainloop(self):
        while True:
            if (button_a.is_pressed() or self.__buttonPin.read_digital()) and self.__state == "waiting": # if the button is pressed and the state is waiting, the buzzer has been pressed and should activate
                self.setActive()
                
                for i in range(3):
                    radio.send_bytes(bytes([50, self.__ID])) # broadcast event to controller and other buzzers (to tell them to deactive)
                    sleep_ms(10)
                    
            radioData = radio.receive_bytes()
            if not radioData:
                continue

            if radioData[0] == 10 or radioData[0] == 25 or radioData[0] == 30 or radioData[0] == 35:
                self.open()
            elif radioData[0] == 15 or radioData[0] == 20:
                self.close()
            elif radioData[0] == 50: # if another buzzer buzzed, we deactivate the buzzer
                if radioData[1] == self.__ID or self.__state == "active": # if this buzzer is already active, we leave it active (that means there's been a lost update, and we leave it to the controller to fix)
                    self.setActive()
                else:
                    self.close()
            elif radioData[0] == 55: # only used if the lost update mentioned above occurs. This allows the controller to reject all but the first buzz, by telling the others to close
                if radioData[1] == self.__ID:
                    self.close()
            elif radioData[0] == 90:
                self.setActive()
            elif radioData[0] == 40: # toggle whether the neopixels should display or not
                self.toggleLight()
            elif radioData[0] == 70: # set whether the neopixels should display or not
                self.toggleLight(radioData[1])
            elif radioData[0] == 45: # update the neopixels, if an error occured
                self.updatePixels()

buzzer = HostBuzzer(pin1, pin0, 7) # setup buzzer object

buzzer.mainloop() # run main event loop
