import radio #type: ignore
from microbit import button_a, pin1, pin0 #type: ignore
from neopixel import NeoPixel
from time import sleep_ms

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

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
        
DEFAULT_COLOR_PROFILE = ColorProfile(ORANGE, BLUE, GREEN, BLACK)

class Buzzer:
    def __init__(self, id, buttonPin, neopixelPin, pixelCount):
        # setup the radio module
        radio.config(group=16, power=7)
        radio.on()

        self.__buttonPin = buttonPin

        self.__displayPixels = True
        self.__pixelCount = pixelCount
        self.__pixels = NeoPixel(neopixelPin, pixelCount)
        self.displayColor(ORANGE)

        self.__ID = id # get the ID before continuing with initialisation

        self.__state = "inactive"
        self.__locked = False

        self.__teamID = None
        self.__colorProfile = DEFAULT_COLOR_PROFILE

    def open(self):
        if self.__locked: # only open the buzer if it wasn't already locked
            self.__state = "locked"
        else:
            self.__state = "waiting"

        self.updatePixels()

    def close(self):
        self.__state = "inactive"
        self.updatePixels()

    def updatePixels(self):
        # get the correct color from ColorProfile object, and make the neopixels display it
        if self.__displayPixels and self.__teamID is not None:
            color = self.__colorProfile.get(self.__state)
            self.displayColor(color)
        else:
            self.displayColor(BLACK)

    def displayColor(self, color):
        for i in range(self.__pixelCount):
            self.__pixels[i] = color
        self.__pixels.show() # type: ignore

    def resetLock(self):
        self.__locked = False
        self.close()

    def lock(self):
        self.__locked = True

    def toggleLight(self, state=None):
        if state is not None:
            self.__displayPixels = state
        else:
            self.__displayPixels = not self.__displayPixels

        self.updatePixels()

    def setActive(self):
        self.__state = "active"
        self.updatePixels()
        
    def loadProfile(self, profileData):
        self.__colorProfile = ColorProfile(list(map(int, profileData[0:3])), list(map(int, profileData[3:6])), list(map(int, profileData[6:9])), list(map(int, profileData[9:12])))
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

            if self.__teamID != None: # these are all commands that require team affiliation, so if the team hasn't been setup, there's no point checking them
                if radioData[0] == 10:
                    self.open()
                elif radioData[0] == 15:
                    self.close()
                elif radioData[0] == 20: # disable the lock - if active, normally used at the end of questions
                    self.resetLock()
                elif radioData[0] == 25: # open the buzzer, but lock if the given teamID matches this buzzer's
                    if radioData[1] == self.__teamID:
                        self.lock()
                    self.open()
                elif radioData[0] == 30: # open the buzzer, but lock if it was currently active
                    if self.__state == "active":
                        self.lock()
                    self.open()
                elif radioData[0] == 35: # only open the buzzer if the buzzer's teamID matches the one supplied
                    if radioData[1] == self.__teamID:
                        self.open()
                elif radioData[0] == 50: # if another buzzer buzzed, we deactivate the buzzer
                    if radioData[1] == self.__ID or self.__state == "active": # if this buzzer is already active, we leave it active (that means there's been a lost update, and we leave it to the controller to fix)
                        self.setActive()
                    else:
                        self.close()
                elif radioData[0] == 55: # only used if the lost update mentioned above occurs. This allows the controller to reject all but the first buzz, by telling the others to close
                    if radioData[1] == self.__ID:
                        self.close()
                elif radioData[0] == 65: # update the colour profile of the buzzer
                    if radioData[1] == self.__teamID and len(radioData) == 14: # input is received as a list of integers (which are sorted into 4 RGB triplets)
                        self.loadProfile(radioData[2:14])
                elif radioData[0] == 85:
                    if radioData[1] == self.__teamID:
                        self.setActive()
                    else:
                        self.close()
                elif radioData[0] == 90:
                    self.setActive()

            if radioData[0] == 40: # toggle whether the neopixels should display or not
                self.toggleLight()
            elif radioData[0] == 70: # set whether the neopixels should display or not
                self.toggleLight(radioData[1])
            elif radioData[0] == 45: # update the neopixels, if an error occured
                self.updatePixels()
            elif radioData[0] == 60: # set the teamID of the buzzer
                if radioData[1] == self.__ID: # only do this if the supplied buzzerID matches this buzzer's
                    self.__teamID = int(radioData[2])
                    self.updatePixels()
            elif radioData[0] == 75: # used to identify a single buzzer to the host and audience
                if radioData[1] == self.__ID:
                    self.setActive()
                else:
                    self.close()
            elif radioData[0] == 80:
                if radioData[1] == self.__ID:
                    self.__teamID = None
                    self.updatePixels()

buzzer = Buzzer("#REPLACE#", pin1, pin0, 7) # setup buzzer object

buzzer.mainloop() # run main event loop
