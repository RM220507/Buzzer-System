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
            
    def close(self):
        for buzzer in self.__buzzers:
            buzzer.close()
            
    @property
    def teamID(self):
        return self.__ID

class Buzzer:
    def __init__(self, ID, teamID, pinIndex):
        self.__ID = ID
        self.__teamID = teamID
        self.__state = "inactive"
        
        self.__isLocked = False
        
        self.__btn = Pin(AVAILABLE_PINS[pinIndex], Pin.IN, Pin.PULL_DOWN)
        self.__btn.irq(handler=self.pressed, trigger=Pin.IRQ_RISING)
        
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
            
    def lock(self):
        self.state = "locked"
        self.__isLocked = True
        
    def open(self):
        if self.__isLocked:
            self.state = "locked"
        else:
            self.state = "waiting"
            self.__btn.irq(handler=self.pressed, trigger=Pin.IRQ_RISING)
            
    def close(self):
        self.state = "inactive"
        self.__btn.irq(handler=None, trigger=Pin.IRQ_RISING)
        
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
        
        self.updatePixels()
    
    def buzzerPressed(self, event, buzzer):
        if not self.__waitingForPress: return
        
        self.close()
        
        self.__activeBuzzer = buzzer
        self.__activeBuzzer.state = "active"
        self.updatePixels()
        
        print(f"buzzed {buzzer.teamID} {buzzer.ID}")
        
    def setupTeams(self, teamArray):
        self.close()
        self.__teams = []
        
        for teamID, pinIndexes, colorProfile in teamArray:
            newTeam = Team(teamID, pinIndexes, colorProfile)
            self.__teams.append(newTeam)
        
        self.updatePixels()
            
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
            else:
                team.close()
        
        self.setActive()
        
    def openLockInd(self):
        if self.__activeBuzzer:
            teamID = self.__activeBuzzer.teamID
            buzzerID = self.__activeBuzzer.ID
        else: # THIS NEEDS BETTER FAIL OVER
            teamID = 0
            buzzerID = 0
            
        for team in self.__teams:
            if team.teamID == teamID:
                team.openLockInd(buzzerID)
            else:
                team.openAll()
                
        self.setActive()
                
    def reset(self):
        for team in self.__teams:
            team.reset()
            
        self.setActive(False)
        
    def close(self):
        self.__activeBuzzer = None
        for team in self.__teams:
            team.close()
            
        self.setActive(False)
        
buzzerController = BuzzerController()

poll_obj = select.poll()
poll_obj.register(sys.stdin, 1)

try:
    while True:
        if poll_obj.poll(0):
            serialInput = sys.stdin.readline()
            command = serialInput.split()
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
            elif command[0] == "reset":
                buzzerController.reset()
            elif command[0] == "close":
                buzzerController.close()
            elif command[0] == "teamSetup":
                allTeams = " ".join(command[1:])
                
                teamArray = []
                for teamStr in allTeams.split(";"):
                    teamStr = teamStr.strip()
                    teamVals = teamStr.split("/")
                    
                    teamID = int(teamVals[0].strip())
                    teamPinIndexes = [int(i) for i in teamVals[1].strip().split()]
                    
                    teamColors = [int(i) for i in teamVals[2].strip().split()]
                    teamColorProfile = {
                        "inactive" : teamColors[0 : 3],
                        "waiting" : teamColors[3 : 6],
                        "active" : teamColors[6 : 9],
                        "locked" : teamColors[9 : 12]
                    }
                    
                    teamData = (teamID, teamPinIndexes, teamColorProfile)
                    teamArray.append(teamData)
                buzzerController.setupTeams(teamArray)
except Exception as e:
    print(e)
    
# teamSetup 0 / 0 1 / 50 50 50 128 128 128 128 0 128 128 0 0; 1 / 2 / 50 50 50 128 128 128 128 0 128 128 0 0