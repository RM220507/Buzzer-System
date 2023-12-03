from machine import Pin
from neopixel import NeoPixel

AVAILABLE_PINS = [14, 13, 12]
PIXELS_PER_BUZZER = 3

class Color:
    BLACK = (0, 0, 0)

class Team:
    def __init__(self, ID, pins, colorProfile):
        self.__ID = ID
        self.__colorProfile = colorProfile
        
        self.__buzzers = []
        for i, pinIndex in enumerate(pins):
            if pinIndex >= len(AVAILABLE_PINS):
                print("Invalid pin")
                continue
            
            newBuzzer = Buzzer(i, self.__ID, pinIndex)
            self.__buzzers.append(newBuzzer)
            
    def updatePixels(self, pixels):
        for buzzer in self.__buzzers:
            buzzer.updatePixels(pixels, self.__colorProfile)

class Buzzer:
    def __init__(self, ID, teamID, pinIndex):
        self.__ID = ID
        self.__teamID = teamID
        self.__state = "inactive"
        
        self.__btn = Pin(AVAILABLE_PINS[pinIndex], Pin.IN, Pin.PULL_DOWN)
        self.__btn.irq(trigger=Pin.IRQ_RISING, handler=self.pressed)
        
        self.__pixels = list(range(pinIndex * PIXELS_PER_BUZZER, (pinIndex * PIXELS_PER_BUZZER) + PIXELS_PER_BUZZER))
        
    def pressed(self, event):
        buzzerController.buzzerPressed(event, self)
        
    def updatePixels(self, pixels, colorProfile):
        for pixel in self.__pixels:
            pixels[pixel] = colorProfile.get(self.__state, Color.BLACK)
        
    @property
    def ID(self):
        return self.__ID
    
    @property
    def teamID(self):
        return self.__teamID
    
    @property
    def state(self):
        return self.__state
    
    @state.setter
    def state(self, newState):
        if newState in ["inactive", "waiting", "active", "locked"]:
            self.__state = newState
        else:
            print("Err: Invalid state")
        
class BuzzerController:
    def __init__(self):
        self.__teams = []
        self.__waitingForPress = True
        
        self.__pixels = NeoPixel(Pin(28), 16)
        self.__pixels.fill(Color.BLACK)
        self.__pixels.write()
        
        self.setupTeams([[0, 1], [2]])
        self.updatePixels()
    
    def buzzerPressed(self, event, buzzer):
        if not self.__waitingForPress:
            return
        
        self.__waitingForPress = False
        self.__activeBuzzer = buzzer
        buzzer.state = "active"
        print(f"Buzzer Pressed: Team {buzzer.teamID}, Buzzer {buzzer.ID}")
        self.updatePixels()
        
    def setupTeams(self, teamArray):
        for i, pins in enumerate(teamArray):
            newTeam = Team(i, pins, {"inactive" : (0, 0, 128), "waiting" : (128, 128, 128), "active" : (0, 128, 0), "locked" : (128, 0, 0)})
            self.__teams.append(newTeam)
            
    def updatePixels(self):
        for team in self.__teams:
            team.updatePixels(self.__pixels)
        self.__pixels.write()
        
buzzerController = BuzzerController()

while True:
    continue
