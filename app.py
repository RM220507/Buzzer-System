import pathlib
import pygubu
import serial
import serial.tools.list_ports as list_ports
import threading
import sqlite3
from pygame import mixer
from teamWidgets import TeamSetup

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "mainUI.ui"

mixer.init()

class Sound:
    INCORRECT = mixer.Sound("sounds/incorrect.mp3")
    CORRECT = mixer.Sound("sounds/correct.mp3")
    BUZZED = mixer.Sound("sounds/buzzer.mp3")

class TeamController:
    def __init__(self, questionController):
        self.__questionController = questionController
        
        self.__teams = []
        
        self.__activeTeam = None
        self.__activeBuzzer = None
        
    def applyActivePenalty(self):
        mixer.Sound.play(Sound.INCORRECT)
        
        for team in self.__teams:
            if team.teamID == self.__activeTeam:
                team.score -= self.__questionController.currentQuestion[4]
                break
            
    def applyActiveScore(self):
        mixer.Sound.play(Sound.CORRECT)
        
        for team in self.__teams:
            if team.teamID == self.__activeTeam:
                team.score += self.__questionController.currentQuestion[3]
                break
                
    def setActive(self, team, buzzer):
        self.__activeTeam = team
        self.__activeBuzzer = buzzer
        
    def clearActive(self):
        self.__activeTeam = None
        self.__activeBuzzer = None
        
    def getActiveAlias(self):
        teamAlias = ""
        buzzerAlias = ""
        activeColor = "#FFFFFF"
        for team in self.__teams:
            if team.teamID == self.__activeTeam:
                teamAlias = team.alias
                buzzerAlias = team.getBuzzerAlias(self.__activeBuzzer)
                activeColor = team.activeColor
                break

        return teamAlias, buzzerAlias, activeColor
        
    def setupTeams(self, teams):
        self.__teams = []
        command = "teamSetup "
        
        for i, team in enumerate(teams):
            newTeam = Team(i, team[0], team[1], team[2])
            command += newTeam.generateCommand()
            
            if i < len(teams) - 1:
                command += "; "
            
            self.__teams.append(newTeam)
            
        return command
            
class Team:
    def __init__(self, ID, alias, colorPalette, buzzers):
        self.__ID = ID
        self.__alias = alias
        
        self.__colorPalette = [Color.HEXtoRGB(col) for col in colorPalette]
        self.__activeTextCol = colorPalette[2]
        
        self.score = 0
        
        self.__buzzers = []
        for i, buzzer in enumerate(buzzers):
            newBuzzer = Buzzer(i, buzzer[0], buzzer[1])
            self.__buzzers.append(newBuzzer)
            
    @property
    def teamID(self):
        return self.__ID
    
    @property
    def alias(self):
        return self.__alias
    
    @property
    def activeColor(self):
        return self.__activeTextCol
            
    def generateCommand(self):
        command = f"{self.__ID} / "
        for buzzer in self.__buzzers:
            command += f"{buzzer.pinIndex} "
            
        command += "/ "
        
        for color in self.__colorPalette:
            for val in color:
                command += f"{val} "
                
        return command
    
    def getBuzzerAlias(self, buzzerID):
        for buzzer in self.__buzzers:
            if buzzer.ID == buzzerID:
                return buzzer.alias
    
class Buzzer:
    def __init__(self, ID, pinIndex, alias):
        self.__ID = ID
        self.__pinIndex = pinIndex
        self.__alias = alias
        
    @property
    def ID(self):
        return self.__ID
    
    @property
    def pinIndex(self):
        return self.__pinIndex
    
    @property
    def alias(self):
        return self.__alias
        
class QuestionManager:
    def __init__(self, db, cursor):
        self.__db = db
        self.__cursor = cursor
        
        self.__rounds = []
        self.__roundID = 0
        
        self.__questions = []
        self.__questionID = 0
        self.__currentQuestion = []
        
        self.__setLoaded = False
        
    def getSets(self):
        self.__cursor.execute("SELECT * FROM QuestionSet")
        return self.__cursor.fetchall()
    
    def loadSet(self, ID):
        self.__setLoaded = True
        
        self.__cursor.execute("SELECT Name FROM QuestionSet WHERE ID = ?", (ID,))
        setName = self.__cursor.fetchone()
        
        self.__cursor.execute("SELECT ID, Name FROM Round, RoundSet WHERE Round.ID = RoundSet.RoundID AND RoundSet.SetID = ? ORDER BY Position", (ID,))
        self.__rounds = self.__cursor.fetchall()
        self.__roundID = 0
        
        self.__setInfo = (setName[0], len(self.__rounds))
        
        self.getQuestions()
        
        return self.currentRound, self.__setInfo
        
    @property
    def currentRound(self):
        if self.__setLoaded:
            return self.__roundID + 1, self.__rounds[self.__roundID][1]
        else:
            return 0, "No Set Loaded"
    
    @property
    def numRounds(self):
        return len(self.__rounds)
    
    def getQuestions(self):
        self.__cursor.execute("SELECT Question, Answer, Notes, CorrectPoints, IncorrectPenalty FROM Question, QuestionRound WHERE Question.ID = QuestionRound.QuestionID AND QuestionRound.RoundID = ? ORDER BY Position", (self.__rounds[self.__roundID][0],))
        self.__questions = self.__cursor.fetchall()
        self.__questionID = 0
        
        for i in range(len(self.__questions)):
            self.__questions[i] = list(self.__questions[i])
            self.__questions[i].append(0)
        self.__currentQuestion = self.__questions[0]
        
    def advanceQuestion(self):
        if not self.__setLoaded:
            self.__currentQuestion =  ["No Set Loaded", "", "", 0, 0, 3]
        else:
            if self.__currentQuestion[5] == 0:
                self.__currentQuestion[5] = 1
            elif self.__currentQuestion[5] == 1:
                self.__questionID += 1
                
                if self.__questionID >= len(self.__questions):
                    self.__roundID += 1
                    if self.__roundID >= len(self.__rounds):
                        self.__currentQuestion = ["Game End", "", "", 0, 0, 3]
                    else:
                        self.__currentQuestion = ["Round Break", "", "", 0, 0, 2]
                else:
                    self.__currentQuestion = self.__questions[self.__questionID]
            elif self.__currentQuestion[5] == 2:
                self.getQuestions()
            elif self.__currentQuestion[5] == 3:
                pass # END OF GAME <- DON'T INCREMENT        
        
        return self.__currentQuestion
    
    @property
    def currentQuestion(self):
        return self.__currentQuestion
            

class SerialController(threading.Thread):
    def __init__(self, readCallback):
        super().__init__(daemon=True)
        
        self.__port = self.findCOMport(516, 3368, 9600)
        if not self.__port.is_open:
            raise ConnectionRefusedError("Micro:bit port not found")
        
        self.__readCallback = readCallback
        
    def findCOMport(self, PID, VID, baud):
        serPort = serial.Serial(baudrate=baud)
        
        ports = list(list_ports.comports())
        for p in ports:
            try:
                if p.pid == PID and p.vid == VID:
                    serPort.port = str(p.device)
                    serPort.open()
            except AttributeError:
                continue
            
        return serPort
        
    def checkBuffer(self):
        return self.__port.in_waiting > 0
    
    def getLine(self):
        return self.__port.readline().decode("utf-8")
    
    def writeLine(self, string):
        self.__port.write(bytes((string + "\n"), "utf-8"))
        
    def run(self):
        while True:
            if self.checkBuffer():
                data = self.getLine()
                self.__readCallback(data)
    
class Color:
    WHITE = "#FFF"
    BLACK = "#000"
    
    @staticmethod
    def HEXtoRGB(value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    
class BuzzerControlApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        
        self.mainwindow = builder.get_object("rootFrame", master)
        self.bigPicture = None
        
        builder.connect_callbacks(self)
        
        #self.refreshQuestionSetDropdown()
        self.showBuzzerClosedFrame()
        self.showBigPictureBlank()
        
        self.__serialController = SerialController(self.buzzCallback)
        
        self.__db = sqlite3.connect("buzzer.db")
        self.__cursor = self.__db.cursor() #type: ignore
        
        self.__questionManager = QuestionManager(self.__db, self.__cursor)
        self.__teamController = TeamController(self.__questionManager)
        
        builder.get_object("currentQuestionLabel").configure(wraplength=800)
        builder.get_object("currentQuestionAnswerLabel").configure(wraplength=800)
        builder.get_object("currentQuestionNotesLabel").configure(wraplength=800)
        
        self.__teamSetupWidget = TeamSetup(builder.get_object("teamSetupTab"), 12, self.setupTeams)
        self.__teamSetupWidget.pack(padx=5, pady=5, expand=True, fill="both")

    def run(self):
        self.__serialController.start()
        
        self.__serialController.writeLine("teamSetup 0 / 0 1 / 50 50 50 128 128 128 128 0 128 128 0 0; 1 / 2 / 50 50 50 128 128 128 128 0 128 128 0 0")
        
        self.mainwindow.mainloop()

    def editQuestionSet(self):
        pass

    def newQuestionSet(self):
        pass

    def loadQuestionSet(self):
        currentRound, setInfo = self.__questionManager.loadSet(1)
        
        self.builder.get_object("questionSetLabel").configure(text=setInfo[0])
        
        self.updateRoundLabel()
        self.updateQuestionLabels(self.__questionManager.currentQuestion)
        
        self.buzzerClose()

        self.showBigPictureTitle()

    def setupTeams(self, teams):
        serialCommand = self.__teamController.setupTeams(teams)
        self.__serialController.writeLine(serialCommand)
    
    def updateRoundLabel(self):
        currentRound = self.__questionManager.currentRound
        numRounds = self.__questionManager.numRounds
        
        self.builder.get_object("roundDescriptor").configure(text=f"{currentRound[1]} - {currentRound[0]} of {numRounds}")
        
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.builder.get_object("bigPictureRoundCountLabel").configure(text=f"Round {currentRound[0]} of {numRounds}")
            self.builder.get_object("bigPictureRoundNameLabel").configure(text=currentRound[1])

    def nextQuestion(self):
        self.clearBuzzerAliasLabel()
        questionData = self.__questionManager.advanceQuestion()
        
        self.buzzerClose()
        self.__teamController.clearActive()
        self.updateQuestionLabels(questionData)
        
        if questionData[5] == 0:
            self.showBigPictureQuestion()
        elif questionData[5] == 1:
            self.showBigPictureBlank()
            self.showBuzzerAdvanceFrame()
        elif questionData[5] == 2:
            self.showBigPictureRound()
            self.showBuzzerAdvanceFrame()

    def updateQuestionLabels(self, questionData):
        self.builder.get_object("questionPointsLabel").configure(text=f"Correct: {questionData[3]}; Penalty: {questionData[4]}")
        self.builder.get_object("currentQuestionLabel").configure(text=questionData[0])
        self.builder.get_object("currentQuestionAnswerLabel").configure(text=questionData[1])
        self.builder.get_object("currentQuestionNotesLabel").configure(text=questionData[2])
        
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.builder.get_object("bigPictureQuestionLabel").configure(text=questionData[0])
        
    def setBigPictureTitle(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            return
        
        self.builder.get_object("bigPictureTitleLabel").configure(text=self.builder.get_object("bigPictureConfTitleEntry").get())
        self.builder.get_object("bigPictureSubtitleLabel").configure(text=self.builder.get_object("bigPictureConfSubtitleEntry").get())

    def toggleBigPictureFullscreen(self):
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.attributes("-fullscreen", not self.bigPicture.attributes("-fullscreen"))
            
    def skipQuestion(self):
        mixer.Sound.play(Sound.INCORRECT)
        self.nextQuestion()

    def buzzerClose(self):
        self.__serialController.writeLine("close")
        self.showBuzzerClosedFrame()
        self.__teamController.clearActive()

    def buzzerOpenAll(self):
        self.__serialController.writeLine("open all")
        self.showBuzzerOpenFrame()
        self.clearBuzzerAliasLabel()
        self.__teamController.clearActive()
        
    def openBigPicture(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            self.bigPicture = self.builder.get_object("bigPictureDisplay", self.mainwindow)
            
            self.builder.get_object("bigPictureQuestionLabel").configure(wraplength=1500, text_color=Color.WHITE)
            self.builder.get_object("bigPictureRoundCountLabel").configure(wraplength=1500, text_color=Color.WHITE)
            self.builder.get_object("bigPictureRoundNameLabel").configure(wraplength=1500, text_color=Color.WHITE)
            self.builder.get_object("bigPictureTitleLabel").configure(wraplength=1500, text_color=Color.WHITE)
            self.builder.get_object("bigPictureSubtitleLabel").configure(wraplength=1500, text_color=Color.WHITE)
            
            self.updateRoundLabel()
            self.updateQuestionLabels(self.__questionManager.currentQuestion)
            
            self.showBigPictureBlank()
        else:
            self.bigPicture.focus()
        
    def showBigPictureTitle(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            return
        
        self.builder.get_object("bigPictureRoundFrame").pack_forget()
        self.builder.get_object("bigPictureQuestionFrame").pack_forget()
        self.builder.get_object("bigPictureTitleFrame").pack(expand=True, fill="both")
    
    def showBigPictureBlank(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            return
        
        self.builder.get_object("bigPictureRoundFrame").pack_forget()
        self.builder.get_object("bigPictureTitleFrame").pack_forget()
        self.builder.get_object("bigPictureQuestionFrame").pack_forget()
        
    def showBigPictureQuestion(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            return
        
        self.builder.get_object("bigPictureQuestionFrame").pack(expand=True, fill="both")
        self.builder.get_object("bigPictureRoundFrame").pack_forget()
        self.builder.get_object("bigPictureTitleFrame").pack_forget()
        
    def showBigPictureRound(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            return
        
        self.builder.get_object("bigPictureQuestionFrame").pack_forget()
        self.builder.get_object("bigPictureRoundFrame").pack(expand=True, fill="both")
        self.builder.get_object("bigPictureTitleFrame").pack_forget()
        
    def showBuzzerOpenFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack(padx=10, pady=10, expand=True, fill="both")
        self.builder.get_object("buzzerControlClosedFrame").pack_forget()
        self.builder.get_object("buzzerControlBuzzedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack_forget()

    def showBuzzerClosedFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack_forget()
        self.builder.get_object("buzzerControlClosedFrame").pack(padx=10, pady=10, expand=True, fill="both")
        self.builder.get_object("buzzerControlBuzzedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack_forget()

    def showBuzzerBuzzedFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack_forget()
        self.builder.get_object("buzzerControlBuzzedFrame").pack(padx=10, pady=10, expand=True, fill="both")
        self.builder.get_object("buzzerControlClosedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack_forget()
        
    def showBuzzerAdvanceFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack_forget()
        self.builder.get_object("buzzerControlBuzzedFrame").pack_forget()
        self.builder.get_object("buzzerControlClosedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack(padx=10, pady=10, expand=True, fill="both")
        
    def buzzerOpenTeam(self):
        self.showBuzzerOpenFrame()
        self.clearBuzzerAliasLabel()
        self.__teamController.clearActive()

    def buzzerOpenLockInd(self):
        self.__serialController.writeLine("open lockInd active")
        self.showBuzzerOpenFrame()
        
        self.clearBuzzerAliasLabel()
        self.__teamController.applyActivePenalty()
        self.__teamController.clearActive()

    def buzzerOpenLockTeam(self):
        self.__serialController.writeLine("open lockTeam active")
        self.showBuzzerOpenFrame()
        
        self.clearBuzzerAliasLabel()
        self.__teamController.applyActivePenalty()
        self.__teamController.clearActive()

    def resetBuzzers(self):
        self.__serialController.writeLine("reset")
        self.showBuzzerClosedFrame()
        self.clearBuzzerAliasLabel()
        self.__teamController.clearActive()
        
    def answeredCorrectly(self):
        self.__teamController.applyActiveScore()
        self.nextQuestion()
    
    def answeredIncorrect(self):
        self.__teamController.applyActivePenalty()
        self.nextQuestion()
    
    def buzzCallback(self, data):
        data = data.split()
        if len(data) >= 3 and data[0] == "buzzed":
            teamID = int(data[1])
            buzzerID = int(data[2])
            self.__teamController.setActive(teamID, buzzerID)
            self.updateBuzzerAliasLabel()
            self.showBuzzerBuzzedFrame()
            mixer.Sound.play(Sound.BUZZED)
            
    def updateBuzzerAliasLabel(self):
        teamAlias, buzzerAlias, activeColor = self.__teamController.getActiveAlias()
        
        self.builder.get_object("buzzerControlBuzzedAliasLabel").configure(text=f"{teamAlias} - {buzzerAlias}")
        
        if not (self.bigPicture is None or not self.bigPicture.winfo_exists()):
            self.builder.get_object("bigPictureBuzzedLabel").configure(text_color=activeColor, text=f"{teamAlias} - {buzzerAlias}")
        
    def clearBuzzerAliasLabel(self):
        self.builder.get_object("buzzerControlBuzzedAliasLabel").configure(text="")
        
        if not (self.bigPicture is None or not self.bigPicture.winfo_exists()):
            self.builder.get_object("bigPictureBuzzedLabel").configure(text="")

if __name__ == "__main__":
    app = BuzzerControlApp()
    app.run()