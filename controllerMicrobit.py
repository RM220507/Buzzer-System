from microbit import uart #type: ignore
import radio #type: ignore

class self:
    def __init__(self):
        uart.init(baudrate=9600)
        
        # setup the radio module
        radio.config(group=16, power=7)
        radio.on()
        
    def mainloop(self):
        while True:
            data = uart.readline()
            if data:
                command = data.split()
                # THE VALIDATION HERE NEEDS TO BE BETTER
                if command[0] == "light":
                    if command[1] == "toggle":
                        self.toggleLight()
                elif command[0] == "open":
                    if command[1] == "all":
                        self.openAll()
                    elif command[1] == "lockTeam":
                        if command[2] == "active":
                            self.openLockTeam()
                        elif command[2].isdigit() and 0 <= int(command[2]) < self.teamCount:
                            self.openLockTeam(int(command[2]))
                    elif command[1] == "team":
                        if command[2].isdigit() and 0 <= int(command[2]) < self.teamCount:
                            self.openTeam(int(command[2]))
                    elif command[1] == "lockInd":
                        if command[2] == "active":
                            self.openLockInd()
                        # ADD ABILITY TO LOCK SPECIFIC INDIVIDUAL
                elif command[0] == "reset":
                    self.reset()
                elif command[0] == "close":
                    self.close()
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
                    self.setupTeams(teamArray)
