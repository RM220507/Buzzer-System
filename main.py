from machine import Pin
from neopixel import NeoPixel
import select
import sys
import time

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
            
    def openAll(self):
        for buzzer in self.__buzzers:
            buzzer.open()
            
    def lockAll(self):
        for buzzer in self.__buzzers:
            buzzer.lock()
            
    def openLockInd(self, buzzerID):
        for buzzer in self.__buzzers:
            if buzzer.ID == buzzerID:
                buzzer.lock()
            else:
                buzzer.open()
                
    def reset(self):
        for buzzer in self.__buzzers:
            buzzer.reset()

class Buzzer:
    def __init__(self, ID, teamID, pinIndex):
        self.__ID = ID
        self.__teamID = teamID
        self.__state = "inactive"
        
        self.__isLocked = False
        
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
            
    def lock(self):
        self.state = "locked"
        self.__isLocked = True
        
    def open(self):
        if self.__isLocked:
            self.state = "locked"
        else:
            self.state = "waiting"
            
    def close(self):
        self.state = "inactive"
        
    def reset(self):
        self.__isLocked = False
        self.close()
        
class BuzzerController:
    def __init__(self):
        self.__teams = []
        self.__waitingForPress = False
        
        self.__pixels = NeoPixel(Pin(28), 16)
        self.__pixels.fill(Color.BLACK)
        self.__pixels.write()
        
        self.__displayLight = True
        
        self.__activeBuzzer = None
        
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
        if self.__displayLight:
            for team in self.__teams:
                team.updatePixels(self.__pixels)
        else:
            self.__pixels.fill(Color.BLACK)
        self.__pixels.write()
        
    def toggleLight(self):
        self.__displayLight = not self.__displayLight
        self.updatePixels()
        
    @property
    def teamCount(self):
        return len(self.__teams)
    
    def openAll(self):
        for team in self.__teams:
            team.openAll()
            
        self.setActive()
        
    def openLockTeam(self, teamID = None):
        if teamID == None and self.__activeBuzzer:
            teamID = self.__activeBuzzer.teamID
        
        for team in self.__teams:
            if team.teamID == teamID:
                team.lockAll()
            else:
                team.openAll()
                
        self.setActive()
    
    def setActive(self, active = True):
        self.__waitingForPress = active
        self.updatePixels()
        
    def openTeam(self, teamID):
        for team in self.__teams:
            if team.teamID == teamID:
                team.openAll()
        
        self.setActive()
        
    def openLockInd(self, teamID = None):
        if teamID == None and self.__activeBuzzer:
            teamID = self.__activeBuzzer.teamID
            
        for team in self.__teams:
            if team.teamID == teamID:
                team.openLockInd(teamID)
            else:
                team.openAll()
                
    def reset(self):
        for team in self.__teams:
            team.reset()
            
        self.setActive(False)
        
    # ADD CLOSE FUNCTION
    # MAKE SURE PIXELS UPDATE WHEN BUZZER PRESSED
        
buzzerController = BuzzerController()

poll_obj = select.poll()
poll_obj.register(sys.stdin, 1)

while True:
    if poll_obj.poll(0):
        serialInput = sys.stdin.readline()
        command = serialInput.split()
        print(command)
        
        # THE VALIDATION HERE NEEDS TO BE BETTER
        if command[0] == "light":
            if command[1] == "toggle":
                buzzerController.toggleLight()
        elif command[0] == "open":
            if command[1] == "all":
                buzzerController.openAll()
            elif command[1] == "lockTeam":
                if command[2] == "active":
                    buzzerController.openLockTeam()
                elif command[2].isdigit() and 0 <= int(command[2]) < buzzerController.teamCount:
                    buzzerController.openLockTeam(int(command[2]))
            elif command[1] == "team":
                if command[2].isdigit() and 0 <= int(command[2]) < buzzerController.teamCount:
                    buzzerController.openTeam(int(command[2]))
            elif command[1] == "lockInd":
                if command[2] == "active":
                    buzzerController.openLockInd()
                # ADD ABILITY TO LOCK SPECIFIC INDIVIDUAL
            elif command[1] == "reset":
                buzzerController.reset()