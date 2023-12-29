from microbit import uart, display #type: ignore
import radio #type: ignore
from micropython import const

# APPLY MINIFIER (https://python-minifier.com/)

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
                if int(radioData[0]) == CommandID.BUZZED:
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
            self.sendMsg([CommandID.RESET_LOCK])
            self.__waitingForBuzz = False
        elif command[0] == "close":
            self.sendMsg([CommandID.CLOSE])
            self.__waitingForBuzz = False
        elif command[0] == "teamSetup":
            teamArray = self.parseTeamInput(command)
            self.__teams = teamArray
            self.setupTeams()
            self.__waitingForBuzz = False
        elif command[0] == "resendTeams":
            self.setupTeams()

    def handleLightCommand(self, command):
        if command[1] == "toggle":
            self.__displayLight = not self.__displayLight
            self.sendMsg([CommandID.LIGHT_SET, int(self.__displayLight)])
        elif command[1] == "set":
            self.__displayLight = bool(int(command[2]))
            self.sendMsg([CommandID.LIGHT_SET, int(self.__displayLight)])
        elif command[1] == "update":
            self.sendMsg([CommandID.LIGHT_UPDATE])

    def handleOpenCommand(self, command):
        if command[1] == "all":
            self.sendMsg([CommandID.OPEN])
            self.__waitingForBuzz = True
        elif command[1] == "lockTeam":
            if command[2] == "active":
                self.sendMsg([CommandID.OPEN_LOCK_TEAM, self.__activeTeam])
                self.__waitingForBuzz = True
            elif command[2].isdigit() and 0 <= int(command[2]) < self.teamCount():
                self.sendMsg([CommandID.OPEN_LOCK_TEAM, int(command[2])])
                self.__waitingForBuzz = True
        elif command[1] == "team":
            if command[2].isdigit() and 0 <= int(command[2]) < self.teamCount():
                self.sendMsg([CommandID.OPEN_TEAM, int(command[2])])
                self.__waitingForBuzz = True
        elif command[1] == "lockInd":
            self.sendMsg([CommandID.OPEN_LOCK_IND])
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
        for team in self.__teams:
            for buzzerID in team[1]:
                self.sendMsg([CommandID.TEAM_ASSIGNMENT, buzzerID, team[0]])

            colorProfileArray = [CommandID.COLOR_PROFILE_ASSIGNMENT, team[0]]
            colorProfileArray.extend(team[2])
            self.sendMsg(colorProfileArray)

    def teamCount(self):
        return len(self.__teams)

display.scroll("Active")
controller = BuzzerController()
controller.mainloop()