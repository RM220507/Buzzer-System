import radio #type: ignore
from microbit import button_a, button_b, pin1, display #type: ignore
from neopixel import NeoPixel
from micropython import const
import time

class CommandID:
    OPEN = const(10)
    CLOSE = const(15)
    RESET_LOCK = const(20)
    OPEN_LOCK_TEAM = const(25)
    OPEN_LOCK_IND = const(30)
    OPEN_TEAM = const(35)
    LIGHT_TOGGLE = const(40)
    LIGHT_UPDATE = const(45)
    BUZZED = const(50)
    IGNORE_BUZZ = const(55)
    TEAM_ASSIGNMENT = const(60)
    COLOR_PROFILE_ASSIGNMENT = const(65)
    LIGHT_SET = const(70)
    IDENTIFY = const(75)
    NOT_NEEDED = const(80)

BLACK = (0, 0, 0)
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
        
DEFAULT_COLOR_PROFILE = ColorProfile(BLACK, BLACK, BLACK, BLACK) # default color palette is all off, so the neopixels aren't on before the buzzer is properly initialised

class Buzzer:
    def __init__(self, neopixelPin, pixelCount):
        # setup the radio module
        radio.config(group=16, power=7)
        radio.on()
        
        self.__ID = self.getID() # get the ID before continuing with initialisation

        self.__displayPixels = True
        #self.__pixelCount = pixelCount
        #self.__pixels = NeoPixel(neopixelPin, pixelCount)

        self.__state = "inactive"
        self.__locked = False
        
        self.__colorProfile = DEFAULT_COLOR_PROFILE

        self.__teamID = None

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
            display.show(self.__state[0])
        else:
            display.clear()

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

    def mainloop(self):
        while True:
            if button_a.is_pressed() and self.__state == "waiting": # if the button is pressed and the state is waiting, the buzzer has been pressed and should activate
                self.setActive()
                radio.send_bytes(bytes([CommandID.BUZZED, self.__ID])) # broadcast event to controller and other buzzers (to tell them to deactive)

            radioData = radio.receive_bytes()
            if not radioData:
                continue
            
            #display.scroll(str(type(radioData[0])))

            if self.__teamID != None: # these are all commands that require team affiliation, so if the team hasn't been setup, there's no point checking them
                if radioData[0] == CommandID.OPEN:
                    self.open()
                elif radioData[0] == CommandID.CLOSE:
                    self.close()
                elif radioData[0] == CommandID.RESET_LOCK: # disable the lock - if active, normally used at the end of questions
                    self.resetLock()
                elif radioData[0] == CommandID.OPEN_LOCK_TEAM: # open the buzzer, but lock if the given teamID matches this buzzer's
                    if radioData[1] == self.__teamID:
                        self.lock()
                    self.open()
                elif radioData[0] == CommandID.OPEN_LOCK_IND: # open the buzzer, but lock if it was currently active
                    if self.__state == "active":
                        self.lock()
                    self.open()
                elif radioData[0] == CommandID.OPEN_TEAM: # only open the buzzer if the buzzer's teamID matches the one supplied
                    if radioData[1] == self.__teamID:
                        self.open()
                elif radioData[0] == CommandID.BUZZED: # if another buzzer buzzed, we deactivate the buzzer
                    if radioData[1] == self.__ID or self.__state == "active": # if this buzzer is already active, we leave it active (that means there's been a lost update, and we leave it to the controller to fix)
                        self.setActive()
                    else:
                        self.close()
                elif radioData[0] == CommandID.IGNORE_BUZZ: # only used if the lost update mentioned above occurs. This allows the controller to reject all but the first buzz, by telling the others to close
                    if radioData[1] == self.__ID:
                        self.close()
                elif radioData[0] == CommandID.COLOR_PROFILE_ASSIGNMENT: # update the colour profile of the buzzer
                    if radioData[1] == self.__teamID and len(radioData) == 14: # input is received as a list of integers (which are sorted into 4 RGB triplets)
                        self.__colorProfile = ColorProfile(radioData[2:5], radioData[5:8], radioData[8:11], radioData[11:14])
                        self.updatePixels()

            if radioData[0] == CommandID.LIGHT_TOGGLE: # toggle whether the neopixels should display or not
                self.toggleLight()
            elif radioData[0] == CommandID.LIGHT_SET: # set whether the neopixels should display or not
                self.toggleLight(radioData[1])
            elif radioData[0] == CommandID.LIGHT_UPDATE: # update the neopixels, if an error occured
                self.updatePixels()
            elif radioData[0] == CommandID.TEAM_ASSIGNMENT: # set the teamID of the buzzer
                if radioData[1] == self.__ID: # only do this if the supplied buzzerID matches this buzzer's
                    self.__teamID = radioData[2]
                    self.updatePixels()
            elif radioData[0] == CommandID.IDENTIFY: # used to identify a single buzzer to the host and audience
                if radioData[1] == self.__ID:
                    self.setActive()
                else:
                    self.close()
            elif radioData[0] == CommandID.NOT_NEEDED:
                self.__teamID = None
                self.updatePixels()
                    
    def getID(self):
        # use the microbits built in buttons to allow the admin to set the buzzer's ID
        ID = 0

        while True:
            if button_a.is_pressed() and button_b.is_pressed():
                break
            elif button_a.is_pressed():
                if ID > 0:
                    ID -= 1
                    display.clear()
                time.sleep(0.3)
            elif button_b.is_pressed():
                if ID < 25:
                    ID += 1
                time.sleep(0.3)

            for i in range(ID):
                display.set_pixel(i//5, i%5, 9)
        display.scroll(f"ID: {ID}. Active")

        return ID
    
buzzer = Buzzer(pin1, 1) # setup buzzer object

buzzer.mainloop() # run main event loop