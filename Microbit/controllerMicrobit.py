from microbit import uart, display #type: ignore
import radio #type: ignore

# APPLY MINIFIER (https://python-minifier.com/)

""" 
class CommandID:
    OPEN = 10
    CLOSE = 15
    RESET_LOCK = 20
    OPEN_LOCK_TEAM = 25
    OPEN_LOCK_IND = 30
    OPEN_TEAM = 35
    LIGHT_TOGGLE = 40
    LIGHT_UPDATE = 45
    BUZZED = 50
    IGNORE_BUZZ = 55
    TEAM_ASSIGNMENT = 60
    COLOR_PROFILE_ASSIGNMENT = 65
    LIGHT_SET = 70
    IDENTIFY = 75 
    NOT_NEEDED = 80
"""

class BuzzerController:
    def __init__(self):
        uart.init(baudrate=9600)

        # setup the radio module
        radio.config(group=16, power=7)
        radio.on()

        self.__teams = []
        self.__waitingForBuzz = False

        self.__displayLight = True

    def sendMsg(self, array):
        radio.send_bytes(bytes(array))

    def teamFromID(self, buzzerID):
        for team in self.__teams:
            for buzzer in team[1]:
                if buzzer == buzzerID:
                    return team[0]

    def mainloop(self):
        serialData = ""
        while True:
            radioData = radio.receive_bytes()
            if radioData:
                if int(radioData[0]) == 50:
                    if self.__waitingForBuzz:
                        self.__waitingForBuzz = False
                        self.__activeBuzzer = radioData[1]
                        self.__activeTeam = self.teamFromID(self.__activeBuzzer)
                        print("buzzed", str(self.__activeTeam), int(self.__activeBuzzer))
                    else:
                        self.sendMsg([55, radioData[1]])

            newByte = uart.read(1)
            if newByte is None:
                continue
            
            newChar = str(newByte, "UTF-8")
            if newChar == "\n":
                self.executeCommand(serialData)
                serialData = ""
            else:
                serialData += newChar

    def executeCommand(self, data):
        command = data.split()

        if len(command) == 0: return
        
        if command[0] == "light":
            self.handleLightCommand(command)
        elif command[0] == "open":
            self.handleOpenCommand(command)
        elif command[0] == "reset":
            self.sendMsg([20])
            self.__waitingForBuzz = False
        elif command[0] == "close":
            self.sendMsg([15])
            self.__waitingForBuzz = False
        elif command[0] == "teamSetup":
            print(command)
            teamArray = self.parseTeamInput(command)
            self.__teams = teamArray
            self.setupTeams()
            self.__waitingForBuzz = False
        elif command[0] == "resendTeams":
            self.setupTeams()
        elif command[0] == "identify":
            if command[1] == "none" or not command[1].isdigit():
                self.sendMsg([15])
            else:
                self.sendMsg([75, int(command[1])])

    def handleLightCommand(self, command):
        if command[1] == "toggle":
            self.__displayLight = not self.__displayLight
            self.sendMsg([70, int(self.__displayLight)])
        elif command[1] == "set":
            self.__displayLight = bool(int(command[2]))
            self.sendMsg([70, int(self.__displayLight)])
        elif command[1] == "update":
            self.sendMsg([45])

    def handleOpenCommand(self, command):
        if command[1] == "all":
            self.sendMsg([10])
            self.__waitingForBuzz = True
        elif command[1] == "lockTeam":
            if command[2] == "active":
                self.sendMsg([25, self.__activeTeam])
                self.__waitingForBuzz = True
            elif command[2].isdigit() and 0 <= int(command[2]) < self.teamCount():
                self.sendMsg([25, int(command[2])])
                self.__waitingForBuzz = True
        elif command[1] == "team":
            if command[2].isdigit() and 0 <= int(command[2]) < self.teamCount():
                self.sendMsg([35, int(command[2])])
                self.__waitingForBuzz = True
        elif command[1] == "lockInd":
            self.sendMsg([30])
            self.__waitingForBuzz = True
                
    def parseTeamInput(self, command):
        allTeams = " ".join(command[1:])

        teamArray = []
        for teamStr in allTeams.split(";"):
            teamStr = teamStr.strip()
            teamVals = teamStr.split("/")

            teamID = int(teamVals[0].strip())
            teamBuzzers = [int(i) for i in teamVals[1].strip().split()]

            teamColors = [int(i) for i in teamVals[2].strip().split()]

            teamData = (teamID, teamBuzzers, teamColors)
            teamArray.append(teamData)
        return teamArray

    def setupTeams(self):
        availableBuzzers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        for team in self.__teams:
            for buzzerID in team[1]:
                self.sendMsg([60, buzzerID, team[0]])
                if buzzerID in availableBuzzers: availableBuzzers.remove(buzzerID)
                
            colorProfileArray = [65, team[0]]
            colorProfileArray.extend(team[2])
            self.sendMsg(colorProfileArray)
            
        for buzzerID in availableBuzzers:
            self.sendMsg([80, buzzerID])
            
        self.sendMsg([70, 1])

    def teamCount(self):
        return len(self.__teams)

display.scroll("Active")
controller = BuzzerController()
controller.mainloop()