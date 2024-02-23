import pathlib
import pygubu
import serial
import serial.tools.list_ports as list_ports
import threading
import sqlite3
from pygame import mixer
from customWidgets import TeamSetup, Selector, BigPicture, HostAidDisplay, HostScoreboard, Soundboard, MacroController
import customtkinter as ctk
from os import path
from tkinter import messagebox
import tkinter as tk
from time import sleep

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "mainUI.ui"

mixer.init()

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
    IDENTIFY_TEAM = 85
    IDENTIFY_ALL = 90

class Sound:
    INCORRECT = mixer.Sound("assets/sounds/incorrect.mp3")
    CORRECT = mixer.Sound("assets/sounds/correct.mp3")
    BUZZED = mixer.Sound("assets/sounds/buzzer.mp3")

    VICTORY = mixer.Sound("assets/sounds/victory.mp3")
    KLAXON = mixer.Sound("assets/sounds/klaxon.mp3")
    TROMBONE = mixer.Sound("assets/sounds/trombone_sad.mp3")
    AWFUL_JOKE = mixer.Sound("assets/sounds/ba_bum_tss.mp3")
    DRUMROLL = mixer.Sound("assets/sounds/drumroll.mp3")
    
    THEME = mixer.Sound("assets/sounds/theme.mp3")

    NAME_ASSIGNMENT = {
        "Theme" : THEME,
        "Buzzer": BUZZED,
        "Correct": CORRECT,
        "Incorrect": INCORRECT,
        "Victory": VICTORY,
        "Klaxon": KLAXON,
        "Sad Trombone": TROMBONE,
        "Ba Dum Crash": AWFUL_JOKE,
        "Drum Roll": DRUMROLL
    }

class TeamController:
    def __init__(self, questionController):
        self.__questionController = questionController

        self.__teams = []

        self.__activeTeam = None
        self.__activeBuzzer = None

        self.__scoreboards = []

    def setScoreboards(self, *widgets):
        self.__scoreboards = widgets

    @property
    def teams(self):
        return self.__teams

    def applyPenalty(self, teamID=None, amount=None):
        if teamID is None:
            teamID = self.__activeTeam
        if amount is None:
            amount = self.__questionController.currentQuestion[4]
        mixer.Sound.play(Sound.INCORRECT)

        for team in self.__teams:
            if team.teamID == teamID:
                team.score -= amount
                break

        self.updateScoreboards()

    def applyScore(self, teamID=None, amount=None):
        if teamID is None:
            teamID = self.__activeTeam
        if amount is None:
            amount = self.__questionController.currentQuestion[3]
        mixer.Sound.play(Sound.CORRECT)

        for team in self.__teams:
            if team.teamID == teamID:
                team.score += amount
                break

        self.updateScoreboards()

    def updateScoreboards(self):
        for scoreboard in self.__scoreboards:
            scoreboard.updateValues(self.__teams)

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
                
                if self.__activeBuzzer == 255:
                    buzzerAlias = "Team"
                else:
                    buzzerAlias = team.getBuzzer(self.__activeBuzzer).alias
                activeColor = team.activeColor
                break

        return teamAlias, buzzerAlias, activeColor

    def getActivePinIndex(self):
        for team in self.__teams:
            if team.teamID == self.__activeTeam:
                return team.getBuzzer(self.__activeBuzzer).pinIndex

    def setupTeams(self, teams):
        self.__teams = []
        commands = []

        availableBuzzers = list(range(25))
        for i, team in enumerate(teams):
            newTeam = Team(i, team[0], team[1], team[2])
            commands.extend(newTeam.generateCommands())
            
            for buzzerID in team[2]: 
                if buzzerID in availableBuzzers:
                    availableBuzzers.remove(buzzerID)

            self.__teams.append(newTeam)
            
        notNeededFirst = [f"{CommandID.NOT_NEEDED} {buzzerID}" for buzzerID in availableBuzzers]
        notNeededFirst.extend(commands)

        return commands

    def getCommands(self):
        commands = []
        for team in self.__teams:
            commands.extend(team.generateCommands())
        return commands

    def getTeamStrings(self):
        strings = []
        for team in self.__teams:
            strings.append(f"{team.teamID} - {team.alias}")
        return strings

    def fromPinIndex(self, pinIndex):
        for team in self.__teams:
            buzzerID = team.fromPinIndex(pinIndex)
            if buzzerID is not None:
                return team.teamID, buzzerID
        return 0, 0

    @property
    def activeTeam(self):
        return self.__activeTeam

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

    def generateCommands(self):
        commands = []
        for buzzer in self.__buzzers:
            commands.append(
                f"{CommandID.TEAM_ASSIGNMENT} {buzzer.pinIndex} {self.__ID}")

        colorCommand = f"{CommandID.COLOR_PROFILE_ASSIGNMENT} {self.__ID} "
        for color in self.__colorPalette:
            for val in color:
                colorCommand += f"{val} "
        commands.append(colorCommand)

        return commands

    def getBuzzer(self, buzzerID):
        for buzzer in self.__buzzers:
            if buzzer.ID == buzzerID:
                return buzzer

    def fromPinIndex(self, pinIndex):
        for buzzer in self.__buzzers:
            if buzzer.pinIndex == pinIndex:
                return buzzer.ID

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
        self.__currentQuestion = ["No Set Loaded", "", "", 0, 0, None, 1]

        self.__setLoaded = False

    def getSets(self):
        self.__cursor.execute("SELECT ID, TechName FROM QuestionSet")
        setList = self.__cursor.fetchall()
        return [f"{entry[0]} - {entry[1]}" for entry in setList]

    def loadSet(self, ID):
        self.__setLoaded = True

        self.__cursor.execute(
            "SELECT Name, Subtitle, TechName FROM QuestionSet WHERE ID = ?", (ID,))
        setName = self.__cursor.fetchone()

        self.__cursor.execute(
            "SELECT ID, Name, DisplayName FROM Round, RoundSet WHERE Round.ID = RoundSet.RoundID AND RoundSet.SetID = ? ORDER BY Position", (ID,))
        self.__rounds = self.__cursor.fetchall()
        self.__roundID = 0

        self.__setInfo = (setName[0], setName[1], len(self.__rounds), setName[2])

        self.getQuestions()
        
        self.__currentQuestion = ["Game Not Started", "Move to Next Question to Start", "", 0, 0, None, 1]
        self.__questionID = -1

        return self.__setInfo

    @property
    def currentRound(self):
        if self.__setLoaded:
            if self.__rounds[self.__roundID][2] is None:
                return self.__roundID + 1, self.__rounds[self.__roundID][1]
            else:
                return self.__roundID + 1, self.__rounds[self.__roundID][2]
        else:
            return 0, "No Set Loaded"

    @property
    def numRounds(self):
        return len(self.__rounds)

    def getQuestions(self):
        self.__cursor.execute(
            "SELECT Question, Answer, Notes, CorrectPoints, IncorrectPenalty, AidPath FROM Question, QuestionRound WHERE Question.ID = QuestionRound.QuestionID AND QuestionRound.RoundID = ? ORDER BY Position", (self.__rounds[self.__roundID][0],))
        self.__questions = self.__cursor.fetchall()
        self.__questionID = 0

        for i in range(len(self.__questions)):
            self.__questions[i] = list(self.__questions[i])
            self.__questions[i].append(0)
        self.__currentQuestion = self.__questions[0]

    def nextRound(self):
        self.__questionID = len(self.__questions)
        self.__roundID += 1
        return self.advanceQuestion()

    def advanceQuestion(self):
        if not self.__setLoaded:
            self.__currentQuestion = ["Game End", "", "", 0, 0, None, 3]
        else:
            if self.__currentQuestion[6] == 0:
                self.__currentQuestion[6] = 1
            elif self.__currentQuestion[6] == 1:
                self.__questionID += 1

                if self.__questionID >= len(self.__questions):
                    self.__roundID += 1
                    if self.__roundID >= len(self.__rounds):
                        self.__roundID = len(self.__rounds) - 1
                        self.__currentQuestion = ["Game End", "", "", 0, 0, None, 3]
                    else:
                        self.__currentQuestion = ["Round Break", self.currentRound[1], "", 0, 0, None, 2]
                else:
                    self.__currentQuestion = self.__questions[self.__questionID]
            elif self.__currentQuestion[6] == 2:
                if self.__roundID >= len(self.__rounds):
                    self.__currentQuestion = ["Game End", "", "", 0, 0, None, 3]
                else:
                    self.getQuestions()
            elif self.__currentQuestion[6] == 3:
                self.__roundID = 0
                self.getQuestions()

        return self.__currentQuestion

    @property
    def currentQuestion(self):
        return self.__currentQuestion

class AidController:
    def __init__(self, hostDisplayParent, bigPictureDisplay=None):
        self.__hostAidDisplay = HostAidDisplay(
            hostDisplayParent, self.show, self.hide, self.play, self.pause, self.stop, self.seek)
        self.__hostAidDisplay.grid(
            row=1, column=1, sticky="nsew", rowspan=3, padx=5, pady=5)

        self.__bigPictureDisplay = bigPictureDisplay

    def setBigPictureDisplay(self, frame):
        self.__bigPictureDisplay = frame

    def unload(self):
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.unload()
            self.hide()
        self.__hostAidDisplay.setLabel("No Aid Available")

    def load(self, file):
        if not path.isfile(file):
            messagebox.showerror("File not Found", f"File {file} is missing")
            self.unload()
            return

        self.__hostAidDisplay.setLabel(file)
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.load(file)
            self.show()
        else:
            self.__hostAidDisplay.setLabel("Open Big Picture Display to use Question Aids")

    def hide(self):
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.setPause(True)
            self.__bigPictureDisplay.pack_forget()

    def show(self):
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.pack(
                expand=True, fill="both", padx=10, pady=10)

    def play(self):
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.play()

    def pause(self):
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.setPause(True)

    def stop(self):
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.stop()

    def seek(self, time):
        if self.__bigPictureDisplay is not None and self.__bigPictureDisplay.winfo_exists():
            self.__bigPictureDisplay.seek(time)

class SerialController(threading.Thread):
    def __init__(self, readCallback):
        super().__init__(daemon=True)
        
        self.attemptConnection()
        
        self.__readCallback = readCallback

    def attemptConnection(self):
        self.__port = self.findCOMport(516, 3368, 9600)
        if not self.__port.is_open:
            self.raiseException()

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

    def raiseException(self):
        askRetry = messagebox.askretrycancel(
            title = "Controller Connection Error",
            message = "No controller micro:bit was detected. Retry?"
        )
        if askRetry:
            self.attemptConnection()

    def run(self):
        while True:
            try:
                if self.checkBuffer():
                    data = self.getLine()
                    self.__readCallback(data)
            except:
                self.raiseException()

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
        self.selectTopLevel = None

        builder.connect_callbacks(self)

        self.showBuzzerClosedFrame()

        self.__serialController = SerialController(self.serialCallback)

        self.__db = sqlite3.connect("buzzer.db")
        self.__cursor = self.__db.cursor()  # type: ignore

        self.__questionManager = QuestionManager(self.__db, self.__cursor)
        self.__teamController = TeamController(self.__questionManager)
        self.__questionAidController = AidController(
            builder.get_object("currentQuestionFrame"))

        builder.get_object("currentQuestionLabel").configure(wraplength=800)
        builder.get_object(
            "currentQuestionAnswerLabel").configure(wraplength=800)
        builder.get_object(
            "currentQuestionNotesLabel").configure(wraplength=800)
        self.builder.get_object("questionSetLabel").configure(wraplength=800)
        
        builder.get_object(
            "buzzerControlClosedTeamSelect").set("")
        builder.get_object(
            "buzzerControlClosedTeamSelect").configure(values=[])

        self.__teamSetupWidget = TeamSetup(builder.get_object("teamSetupTab"), 16, self.setupTeams, self.loadColorPalettePrompt,
                                        self.saveColorPalette, self.saveTeamConfiguration, self.loadTeamConfigurationPrompt, self.buzzerIdentify, self.buzzerIdentifyAll)
        self.__teamSetupWidget.pack(padx=5, pady=5, expand=True, fill="both")

        self.__scoreboardWidget = HostScoreboard(
            builder.get_object("scoreTab"), self.__teamController)
        self.__scoreboardWidget.pack(padx=5, pady=5, expand=True, fill="both")

        self.__teamController.setScoreboards(self.__scoreboardWidget)

        self.__soundboardWidget = Soundboard(
            builder.get_object("soundboardTab"), Sound)
        self.__soundboardWidget.pack(padx=5, pady=5, expand=True, fill="both")

        commands = {
            "Host: Display Hosting Tab": lambda: self.builder.get_object("mainTabview").set("Hosting"),
            "Host: Display Big Picture Tab": lambda: self.builder.get_object("mainTabview").set("Big Picture"),
            "Host: Display Team Setup Tab": lambda: self.builder.get_object("mainTabview").set("Team Setup"),
            "Host: Display Scoreboard Tab": lambda: self.builder.get_object("mainTabview").set("Scoreboard"),
            "Host: Display Soundboard Tab": lambda: self.builder.get_object("mainTabview").set("Soundboard"),
            "Host: Display Buzzer Functions Tab": lambda: self.builder.get_object("mainTabview").set("Buzzer Functions"),
            "Host: Display Macros Tab": lambda: self.builder.get_object("mainTabview").set("Macros"),
            "Big Picture: Open": self.openBigPicture,
            "Big Picture: Display Question": self.showBigPictureQuestion,
            "Big Picture: Display Round": self.showBigPictureRound,
            "Big Picture: Display Title": self.showBigPictureTitle,
            "Big Picture: Display Scoreboard": self.showBigPictureScoreboard,
            "Big Picture: Display Blank": self.showBigPictureBlank,
            "Soundboard: Play Correct": lambda: self.__soundboardWidget.play("Correct"),
            "Soundboard: Play Incorrect": lambda: self.__soundboardWidget.play("Incorrect"),
            "Soundboard: Play Buzzer": lambda: self.__soundboardWidget.play("Buzzer"),
            "Soundboard: Play Victory": lambda: self.__soundboardWidget.play("Victory"),
            "Soundboard: Play Klaxon": lambda: self.__soundboardWidget.play("Klaxon"),
            "Soundboard: Play Sad Trombone": lambda: self.__soundboardWidget.play("Sad Trombone"),
            "Soundboard: Play Ba Dum Crash": lambda: self.__soundboardWidget.play("Ba Dum Crash"),
            "Soundboard: Play Drum Roll": lambda: self.__soundboardWidget.play("Drum Roll"),
            "Soundboard: Stop": self.__soundboardWidget.stop,
            "Buzzer Functions: Resend": self.buzzerFuncResend,
            "Buzzer Functions: Lights On": self.buzzerFuncLightOn,
            "Buzzer Functions: Lights Off": self.buzzerFuncLightOff,
            "Buzzer Functions: Update Lights": self.buzzerFuncLightUpdate
        }
        self.__macroController = MacroController(
            builder.get_object("macroTab"), commands, 6)
        self.__macroController.pack(padx=5, pady=5, fill="both", expand=True)

    def run(self):
        self.__serialController.start()

        self.mainwindow.mainloop()

    def loadQuestionSet(self, value):
        setID = int(value.split()[0])

        setInfo = self.__questionManager.loadSet(setID)

        self.builder.get_object("questionSetLabel").configure(text=f"{setInfo[3]} - {setInfo[0]}")
        self.updateRoundLabel()
        self.updateQuestionLabels(self.__questionManager.currentQuestion)

        self.buzzerClose()
        self.showBuzzerAdvanceFrame()

        if self.builder.get_object("bigPictureConfTitleEntry").get() == "":
            self.builder.get_object("bigPictureConfTitleEntry").delete(0, tk.END)
            self.builder.get_object("bigPictureConfSubtitleEntry").delete(0, tk.END)
            
            self.builder.get_object("bigPictureConfTitleEntry").insert(0, setInfo[0])
            self.builder.get_object("bigPictureConfSubtitleEntry").insert(0, setInfo[1])
            

        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.setBigPictureTitle()
            self.bigPicture.displayTitle()

    def loadQuestionSetPrompt(self):
        setList = self.__questionManager.getSets()

        self.selectTopLevel = Selector(
            self.mainwindow, setList, self.loadQuestionSet)

    def loadColorPalette(self, value, teamElement):
        paletteID = int(value.split()[0])

        self.__cursor.execute(
            "SELECT InactiveColor, WaitingColor, ActiveColor, LockedColor FROM ColorPalette WHERE ID = ?", (paletteID,))
        colorPalette = self.__cursor.fetchone()

        teamElement.loadPalette(colorPalette)

    def loadColorPalettePrompt(self, teamElement):
        self.__cursor.execute("SELECT ID, Name FROM ColorPalette")
        paletteList = self.__cursor.fetchall()
        paletteList = [f"{entry[0]} - {entry[1]}" for entry in paletteList]

        self.selectTopLevel = Selector(
            self.mainwindow, paletteList, self.loadColorPalette, (teamElement,))

    def saveColorPalette(self, teamElement):
        inputDialog = ctk.CTkInputDialog(
            title="Colour Palette Name", text="Name your Colour Palette")
        name = inputDialog.get_input()[:30]  # type: ignore

        inactiveColor, waitingColor, activeColor, lockedColor = teamElement.getColors()

        self.__cursor.execute(
            "SELECT 1 FROM ColorPalette WHERE Name = ?", (name,))
        if self.__cursor.fetchone():
            self.__cursor.execute("UPDATE ColorPalette SET InactiveColor = ?, WaitingColor = ?, ActiveColor = ?, LockedColor = ? WHERE Name = ?", (
                inactiveColor, waitingColor, activeColor, lockedColor, name))
        else:
            self.__cursor.execute("INSERT INTO ColorPalette (Name, InactiveColor, WaitingColor, ActiveColor, LockedColor) VALUES (?, ?, ?, ?, ?)", (
                name, inactiveColor, waitingColor, activeColor, lockedColor))
        self.__db.commit()  # type: ignore

    def loadTeamConfigurationPrompt(self):
        self.__cursor.execute("SELECT ID, Name FROM Configuration")
        configList = self.__cursor.fetchall()
        configList = [f"{entry[0]} - {entry[1]}" for entry in configList]

        self.selectTopLevel = Selector(
            self.mainwindow, configList, self.loadTeamConfiguration)

    def loadTeamConfiguration(self, value):
        configID = int(value.split()[0])

        self.__cursor.execute(
            "SELECT ID, Name FROM TeamConfig WHERE ConfigID = ?", (configID,))
        teams = self.__cursor.fetchall()

        configData = []
        for team in teams:
            self.__cursor.execute(
                "SELECT ID, Alias FROM BuzzerTeam WHERE TeamID = ?", (team[0],))
            teamBuzzers = self.__cursor.fetchall()

            # could be used for color palette later
            teamData = (team[1], None, teamBuzzers)
            configData.append(teamData)

        self.__teamSetupWidget.loadConfig(configData)

    def saveTeamConfiguration(self, config):
        inputDialog = ctk.CTkInputDialog(
            title="Configuration Name", text="Name your Configuration")
        name = inputDialog.get_input()[:30]  # type: ignore

        self.__cursor.execute(
            "SELECT 1 FROM Configuration WHERE Name = ?", (name,))
        if self.__cursor.fetchone():
            self.__cursor.execute(
                "SELECT ID FROM Configuration WHERE Name = ?", (name,))
            configID = self.__cursor.fetchone()[0]

            self.__cursor.execute(
                "SELECT ID FROM TeamConfig WHERE ConfigID = ?", (configID,))
            teamIDs = self.__cursor.fetchall()
            self.__cursor.execute(
                "DELETE FROM TeamConfig WHERE ConfigID = ?", (configID,))
            self.__cursor.executemany(
                "DELETE FROM BuzzerTeam WHERE TeamID = ?", teamIDs)
        else:
            self.__cursor.execute(
                "INSERT INTO Configuration (Name) VALUES (?)", (name,))
            self.__cursor.execute(
                "SELECT last_insert_rowid() FROM Configuration")
            configID = self.__cursor.fetchone()[0]

        teams = config[0]
        buzzers = config[1]

        teamIDs = []
        for team in teams:
            self.__cursor.execute(
                "INSERT INTO TeamConfig (Name, ConfigID) VALUES (?, ?)", (team, configID))
            self.__cursor.execute("SELECT last_insert_rowid() FROM TeamConfig")
            teamIDs.append(self.__cursor.fetchone()[0])

        for buzzer in buzzers:
            self.__cursor.execute(
                "INSERT INTO BuzzerTeam VALUES (?, ?, ?)", (buzzer[0], teamIDs[buzzer[1]], buzzer[2]))

        self.__db.commit()  # type: ignore

    def setupTeams(self, teams):
        commands = self.__teamController.setupTeams(teams)
        teamData = self.__teamController.getTeamStrings()
        self.builder.get_object(
            "buzzerControlClosedTeamSelect").configure(values=teamData)
        
        if len(teamData) > 0:
            self.builder.get_object(
                "buzzerControlClosedTeamSelect").set(teamData[0])

            commandString = ";".join(commands)
            if len(commandString) > 50:              
                separatedCommands = [commands[0]]
                currentIndex = 0
                for command in commands[1:]:
                    if len(separatedCommands[currentIndex]) + len(command) + 1 > 50:
                        currentIndex += 1
                        separatedCommands.append(command)
                    else:
                        separatedCommands[currentIndex] += f";{command}"
                        
                for smallCommand in separatedCommands:
                    self.__serialController.writeLine(smallCommand)
                    sleep(0.5)
            else:
                self.__serialController.writeLine(commandString)

        self.__scoreboardWidget.updateValues(self.__teamController.teams)

    def updateRoundLabel(self):
        currentRound = self.__questionManager.currentRound
        numRounds = self.__questionManager.numRounds

        self.builder.get_object("roundDescriptor").configure(
            text=f"{currentRound[1]} - {currentRound[0]} of {numRounds}")

        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.updateRound(
                currentRound[0], numRounds, currentRound[1])

    def nextQuestion(self):
        questionData = self.__questionManager.advanceQuestion()
        self.handleNextQuestion(questionData)
        self.__serialController.writeLine(f"{CommandID.RESET_LOCK}")

    def handleNextQuestion(self, questionData):
        self.clearBuzzerAliasLabel()
        self.buzzerClose()
        self.__teamController.clearActive()
        self.updateQuestionLabels(questionData)

        if questionData[6] == 0:
            self.showBigPictureQuestion()
            self.updateRoundLabel()
        elif questionData[6] == 1:
            self.showBigPictureBlank()
            self.showBuzzerAdvanceFrame()
        elif questionData[6] == 2:
            self.updateRoundLabel()
            self.showBigPictureRound()
            self.showBuzzerAdvanceRoundFrame()
        elif questionData[6] == 3:
            self.updateRoundLabel()

    def updateQuestionLabels(self, questionData):
        self.builder.get_object("questionPointsLabel").configure(
            text=f"Correct: {questionData[3]}; Penalty: {questionData[4]}")
        self.builder.get_object("currentQuestionLabel").configure(
            text=questionData[0])
        self.builder.get_object("currentQuestionAnswerLabel").configure(
            text=questionData[1])
        self.builder.get_object("currentQuestionNotesLabel").configure(
            text=questionData[2])

        if questionData[5]:
            self.__questionAidController.load(questionData[5])
        else:
            self.__questionAidController.unload()

        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.updateQuestion(questionData[0])

    def setBigPictureTitle(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            return

        self.bigPicture.updateTitle(self.builder.get_object("bigPictureConfTitleEntry").get(
        ), self.builder.get_object("bigPictureConfSubtitleEntry").get())

    def toggleBigPictureFullscreen(self):
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.toggleFullscreen()

    def showBigPictureBlank(self):
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.displayBlank()

    def showBigPictureQuestion(self):
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.displayQuestion()

    def showBigPictureRound(self):
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.displayRound()

    def showBigPictureTitle(self):
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.displayTitle()

    def showBigPictureScoreboard(self):
        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.displayScoreboard()

    def skipQuestion(self):
        #mixer.Sound.play(Sound.INCORRECT)
        self.nextQuestion()
        
    def skipRound(self):
        nextQuestion = self.__questionManager.nextRound()
        self.handleNextQuestion(nextQuestion)

    def buzzerClose(self):
        self.__serialController.writeLine(f"{CommandID.CLOSE}")
        self.showBuzzerClosedFrame()
        self.__teamController.clearActive()

    def buzzerOpenAll(self):
        self.__serialController.writeLine(f"{CommandID.OPEN}")
        self.showBuzzerOpenFrame()
        self.clearBuzzerAliasLabel()
        self.__teamController.clearActive()
        
    def buzzerReopenAll(self):
        self.answeredIncorrect()
        self.buzzerOpenAll()

    def openBigPicture(self):
        if self.bigPicture is None or not self.bigPicture.winfo_exists():
            self.bigPicture = BigPicture(self.mainwindow)

            self.__questionAidController.setBigPictureDisplay(
                self.bigPicture.aidDisplay)

            self.__teamController.setScoreboards(
                self.__scoreboardWidget, self.bigPicture.scoreboardFrame)
            self.__teamController.updateScoreboards()

            self.updateRoundLabel()
            self.updateQuestionLabels(self.__questionManager.currentQuestion)

            self.setBigPictureTitle()

            self.bigPicture.displayBlank()
        else:
            self.bigPicture.focus()

    def showBuzzerOpenFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack(
            padx=10, pady=10, expand=True, fill="both")
        self.builder.get_object("buzzerControlClosedFrame").pack_forget()
        self.builder.get_object("buzzerControlBuzzedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceRoundFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack_forget()

    def showBuzzerClosedFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack_forget()
        self.builder.get_object("buzzerControlClosedFrame").pack(
            padx=10, pady=10, expand=True, fill="both")
        self.builder.get_object("buzzerControlBuzzedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceRoundFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack_forget()

    def showBuzzerBuzzedFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack_forget()
        self.builder.get_object("buzzerControlBuzzedFrame").pack(
            padx=10, pady=10, expand=True, fill="both")
        self.builder.get_object("buzzerControlClosedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceRoundFrame").pack_forget()

    def showBuzzerAdvanceFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack_forget()
        self.builder.get_object("buzzerControlBuzzedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceRoundFrame").pack_forget()
        self.builder.get_object("buzzerControlClosedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack(
            padx=10, pady=10, expand=True, fill="both")
        
    def showBuzzerAdvanceRoundFrame(self):
        self.builder.get_object("buzzerControlWaitingFrame").pack_forget()
        self.builder.get_object("buzzerControlBuzzedFrame").pack_forget()
        self.builder.get_object("buzzerControlClosedFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceFrame").pack_forget()
        self.builder.get_object("buzzerControlAdvanceRoundFrame").pack(
            padx=10, pady=10, expand=True, fill="both")

    def buzzerOpenTeam(self):
        selectValue = self.builder.get_object(
            "buzzerControlClosedTeamSelect").get()
        if selectValue == "CTkOptionMenu":
            return

        teamID = int(selectValue.split(" - ")[0])
        self.__serialController.writeLine(f"{CommandID.OPEN_TEAM} {teamID}")
        self.showBuzzerOpenFrame()

        self.clearBuzzerAliasLabel()
        self.__teamController.clearActive()

    def buzzerOpenLockInd(self):
        self.__serialController.writeLine(
            f"{CommandID.OPEN_LOCK_IND} {self.__teamController.getActivePinIndex()}")
        self.showBuzzerOpenFrame()

        self.clearBuzzerAliasLabel()
        self.__teamController.applyPenalty()
        self.__teamController.clearActive()

    def buzzerOpenLockTeam(self):
        self.__serialController.writeLine(
            f"{CommandID.OPEN_LOCK_TEAM} {self.__teamController.activeTeam}")
        self.showBuzzerOpenFrame()

        self.clearBuzzerAliasLabel()
        self.__teamController.applyPenalty()
        self.__teamController.clearActive()

    def resetBuzzers(self):
        self.__serialController.writeLine(f"{CommandID.RESET_LOCK}")
        self.showBuzzerClosedFrame()
        self.clearBuzzerAliasLabel()
        self.__teamController.clearActive()

    def answeredCorrectly(self):
        self.__teamController.applyScore()
        self.nextQuestion()

    def answeredIncorrect(self):
        self.__teamController.applyPenalty()
        self.nextQuestion()

    def serialCallback(self, string):
        print(string)
        data = string.split()
        if len(data) >= 2 and data[0] == "buzzed" and data[1].isdigit():
            teamID, buzzerID = self.__teamController.fromPinIndex(int(data[1]))
            self.__teamController.setActive(teamID, buzzerID)
            self.updateBuzzerAliasLabel()
            self.showBuzzerBuzzedFrame()
            mixer.Sound.play(Sound.BUZZED)
        elif len(data) >= 2 and data[0] == "macro" and data[1].isdigit():
            self.__macroController.execute(int(data[1]))
        elif data[0] == "ERROR:":
            messagebox.showerror("Command Error", string)
            
    def updateBuzzerAliasLabel(self):
        teamAlias, buzzerAlias, activeColor = self.__teamController.getActiveAlias()

        self.builder.get_object("buzzerControlBuzzedAliasLabel").configure(
            text=f"{teamAlias} - {buzzerAlias}")

        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.updateBuzzerAlias(
                f"{teamAlias} - {buzzerAlias}", activeColor)

    def clearBuzzerAliasLabel(self):
        self.builder.get_object(
            "buzzerControlBuzzedAliasLabel").configure(text="")

        if self.bigPicture is not None and self.bigPicture.winfo_exists():
            self.bigPicture.updateBuzzerAlias("")

    def buzzerIdentify(self, buzzerID):
        self.__serialController.writeLine(f"{CommandID.IDENTIFY} {buzzerID}")
        
    def buzzerIdentifyTeam(self):
        selectValue = self.builder.get_object(
            "buzzerControlClosedTeamSelect").get()
        if selectValue == "CTkOptionMenu" or selectValue == "":
            return

        teamID = int(selectValue.split(" - ")[0])
        self.__serialController.writeLine(f"{CommandID.IDENTIFY_TEAM} {teamID}")
        
        self.__teamController.setActive(teamID, 255)
        self.updateBuzzerAliasLabel()
        self.showBuzzerBuzzedFrame()
        
    def buzzerStopIdentifyTeam(self):
        self.__serialController.writeLine(f"{CommandID.IDENTIFY_TEAM} 255")
        
    def buzzerFuncResend(self):
        commands = self.__teamController.getCommands()
        self.__serialController.writeLine(";".join(commands))

    def buzzerFuncLightOn(self):
        self.__serialController.writeLine(f"{CommandID.LIGHT_SET} 1")

    def buzzerFuncLightOff(self):
        self.__serialController.writeLine(f"{CommandID.LIGHT_SET} 0")

    def buzzerFuncLightUpdate(self):
        self.__serialController.writeLine(f"{CommandID.LIGHT_UPDATE}")
        
    def buzzerIdentifyAll(self):
        self.__serialController.writeLine(f"{CommandID.IDENTIFY_ALL}")


if __name__ == "__main__":
    app = BuzzerControlApp()
    app.run()