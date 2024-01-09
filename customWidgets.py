import customtkinter as ctk
from tkinter.colorchooser import askcolor
import tkinter as tk
from tkinter import messagebox
import vlc
from pygame import mixer

mixer.init()

class Color:
    WHITE = "#FFF"
    BLACK = "#000"
    
class Font:
    def __init__(self):
        self.LARGE = ctk.CTkFont("Bahnschrift Semibold", 72, "bold", "roman")
        self.SMALL = ctk.CTkFont("Bahnschrift Semibold", 36, "bold", "roman")
    
class MacroController(ctk.CTkFrame):
    def __init__(self, master, commands, count, **kwargs):
        super().__init__(master, **kwargs)
        
        self.__commands = commands
        self.__count = count
        
        self.__commandBind = ["No Macro Selected" for i in range(self.__count)]
        
        self.__selector = None
        
        self.__btns = []
        for i in range(self.__count):
            btn = ctk.CTkButton(self, text=self.__commandBind[i], command= lambda ix=i: self.setPrompt(ix))
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            self.__btns.append(btn)
            
        
    def execute(self, id):
        if 0 <= id < len(self.__commandBind):
            command = self.__commands.get(self.__commandBind[id])
            if command is not None:
                command()
                
    def setPrompt(self, id):
        if self.__selector is not None and self.__selector.winfo_exists():
            self.__selector.destroy()
        self.__selector = Selector(self.master, list(self.__commands.keys()), self.set, (id,))
    
    def set(self, value, id):
        if self.__selector is not None:
            self.__selector.destroy()
        
        self.__commandBind[id] = value
        self.__btns[id].configure(text=value)
        
class Soundboard(ctk.CTkFrame):
    def __init__(self, master, sounds, **kwargs):
        super().__init__(master, **kwargs)
        
        self.columnconfigure((0, 1, 2, 3), weight=1)
        self.rowconfigure((0, 1, 2, 3), weight=1)
        
        self.__sounds = sounds
        
        ctk.CTkButton(self, text="Stop All Sounds", command=self.stop).grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        for i, sound in enumerate(self.__sounds.NAME_ASSIGNMENT):
            btn = ctk.CTkButton(self, text=sound, command= lambda x=sound: self.play(x))
            btn.grid(row=(i//4)+1, column=i%4, padx=5, pady=5, sticky="nsew")
    
    def play(self, sound):
        mixer.Sound.play(self.__sounds.NAME_ASSIGNMENT[sound])
        
    def stop(self):
        mixer.stop()
        
class HostScoreboard(ctk.CTkFrame):
    def __init__(self, master, teamController, **kwargs):
        super().__init__(master, **kwargs)
        
        self.__teamController = teamController
        
        self.manualControlFrame = ctk.CTkFrame(self)
        self.manualControlFrame.pack(padx=5, pady=5, fill="x")
        
        self.manualControlFrame.columnconfigure(0, weight=3)
        self.manualControlFrame.columnconfigure(1, weight=1)
        
        self.manualControlTeamDropdown = ctk.CTkOptionMenu(self.manualControlFrame, values=self.__teamController.getTeamStrings())
        self.manualControlTeamDropdown.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.manualControlTeamDropdown.set("Select Team")
        
        self.manualControlAmountEntry = ctk.CTkEntry(self.manualControlFrame, placeholder_text="Amount")
        self.manualControlAmountEntry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        ctk.CTkButton(self.manualControlFrame, text="+", command=lambda: self.changeScore(True)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.manualControlFrame, text="-", command=lambda: self.changeScore(False)).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.scoreboard = Scoreboard(self, False)
        self.scoreboard.pack(padx=5, pady=5, expand=True, fill="both")

    def changeScore(self, bonus=True):
        selectVal = self.manualControlTeamDropdown.get()
        if selectVal == "Select Team":
            messagebox.showerror("Value Error", "Team must be selected")
            return
        
        teamID = int(selectVal.split(" - ")[0])
        
        amount = self.manualControlAmountEntry.get()
        if amount.isdigit():
            if bonus:
                self.__teamController.applyScore(teamID, int(amount))
            else:
                self.__teamController.applyPenalty(teamID, int(amount))
                
            self.manualControlTeamDropdown.set("Select Team")
            self.manualControlAmountEntry.delete(0, tk.END)
        else:
            messagebox.showerror("Value Error", "Amount must be an integer")
            
    def updateValues(self, teams):
        self.manualControlTeamDropdown.configure(values=self.__teamController.getTeamStrings())

        self.scoreboard.updateValues(teams)
        
class BigPictureScoreboard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg_color=Color.BLACK, fg_color=Color.BLACK, **kwargs)
        
        fonts = Font()
        
        ctk.CTkLabel(self, text="Scoreboard", font=fonts.LARGE, text_color=Color.WHITE).pack(padx=5, pady=5, fill="x")
        
        self.scoreboard = Scoreboard(self, True)
        self.scoreboard.pack(padx=5, pady=5, expand=True, fill="both")

    def updateValues(self, teams):
        self.scoreboard.updateValues(teams)
            
class Scoreboard(ctk.CTkScrollableFrame):
    def __init__(self, master, darkMode, **kwargs):
        super().__init__(master, width=300, height=400, **kwargs)
        
        self.__darkMode = darkMode
        
        if self.__darkMode:
            self.configure(bg_color=Color.BLACK, fg_color=Color.BLACK)
        
    def getScores(self, teams):
        teamDict = {}
        for team in teams:
            teamDict[team.alias] = team.score
        return teamDict
        
    def getSortedScores(self, teams):
        teamDict = self.getScores(teams)
        
        sortedScores = sorted(teamDict.items(), key=lambda x:x[1], reverse=True)
        return sortedScores
        
    def updateValues(self, teams):
        scores = self.getSortedScores(teams)
        
        for child in self.winfo_children(): child.destroy()
        
        for score in scores:
            newElement = ScoreboardTeamElement(self, score[0], score[1], self.__darkMode)
            newElement.pack(padx=5, pady=5, fill="x")
            
class ScoreboardTeamElement(ctk.CTkFrame):
    def __init__(self, master, name, score, darkMode, **kwargs):
        super().__init__(master, **kwargs)
        
        fonts = Font()
        
        nameLabel = ctk.CTkLabel(self, text=name, font=fonts.LARGE)
        nameLabel.pack(padx=5, pady=5, side="left")
        
        scoreLabel = ctk.CTkLabel(self, text=str(score), font=fonts.LARGE)
        scoreLabel.pack(padx=5, pady=5, side="right")
        
        if darkMode:
            self.configure(bg_color=Color.BLACK, fg_color=Color.BLACK)
            nameLabel.configure(text_color=Color.WHITE)
            scoreLabel.configure(text_color=Color.WHITE)
    
class HostAidDisplay(ctk.CTkFrame):
    def __init__(self, master, showCallback, hideCallback, playCallback, pauseCallback, stopCallback, seekCallback, **kwargs):
        super().__init__(master, **kwargs)
        
        self.visibilityFrame = ctk.CTkFrame(self)
        self.visibilityFrame.pack(padx=5, pady=5, fill="x")
        self.visibilityFrame.columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(self.visibilityFrame, text="Show", command=showCallback).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.visibilityFrame, text="Hide", command=hideCallback).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.mediaControlFrame = ctk.CTkFrame(self)
        self.mediaControlFrame.pack(padx=5, pady=5, fill="x")
        self.mediaControlFrame.columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkButton(self.mediaControlFrame, text="Play", command=playCallback).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.mediaControlFrame, text="Pause", command=pauseCallback).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.mediaControlFrame, text="Stop", command=stopCallback).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.seekCallback = seekCallback
        
        self.seekTimeEntry = ctk.CTkEntry(self.mediaControlFrame, placeholder_text="Time (seconds)")
        self.seekTimeEntry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ctk.CTkButton(self.mediaControlFrame, text="Seek", command=self.seek).grid(row=1, column=2, padx=5, pady=5, sticky="ew")

    def seek(self):
        value = self.seekTimeEntry.get()
        try:
            value = float(value)
            self.seekCallback(value)
        except ValueError:
            messagebox.showerror("Value Error", "Time must be a number (integer or decimal)")

class BigPictureAidDisplay(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs, bg_color=Color.BLACK, fg_color=Color.BLACK)
        self.settings = { # Inizialazing dictionary settings
            "width" : 1024,
            "height" : 576
        }
        self.settings.update(kwargs) # Changing the default settings
        self.video_source =  ""

        # Canvas where to draw video output
        self.canvas = tk.Canvas(self, bg = "black", width=self.settings["width"], height=self.settings["height"], highlightthickness = 0)
        self.canvas.pack(fill="both")

        # Creating VLC player
        #vlcPath = ""
        #self.instance = vlc.Instance(f"--vlc-path={vlcPath}")
        self.instance = vlc.Instance() #! THIS NEEDS TO BE CHANGED
        self.player = self.instance.media_player_new() # pyright: ignore[reportOptionalMemberAccess]

    def GetHandle(self):
        # Getting frame ID
        return self.winfo_id()

    def load(self, _source):
        # Function to start player from given source
        Media = self.instance.media_new(_source) # pyright: ignore[reportOptionalMemberAccess]
        Media.get_mrl()
        self.player.set_media(Media)
        self.player.set_hwnd(self.GetHandle())
        
        self.play()
        self.stop()

    def play(self):
        self.player.play()
        
    def togglePause(self):
        self.player.pause()
        
    def setPause(self, doPause):
        self.player.set_pause(doPause)
        
    def stop(self):
        self.setPause(True)
        self.player.set_time(0)
        
    def unload(self):
        self.load("assets/blank.png")
        
    def seek(self, time):
        time_ms = time * 1000
        if time_ms <= self.player.get_length():
            self.player.set_time(int(time_ms))
        else:
            messagebox.showerror("Time Error", "Time supplied is beyond end of media")

class BigPicture(ctk.CTkToplevel):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color=Color.BLACK)
        
        fonts = Font()
        
        # QUESTION FRAME
        self.questionFrame = ctk.CTkFrame(self, bg_color=Color.BLACK, corner_radius=0, fg_color=Color.BLACK)
        
        self.questionLabel = ctk.CTkLabel(self.questionFrame, text="", font=fonts.LARGE, wraplength=1500, text_color=Color.WHITE)
        self.questionLabel.pack(expand=True, side="top")
        
        self.aidDisplay = BigPictureAidDisplay(self.questionFrame)
        self.aidDisplay.pack(expand=True, fill="both", padx=10, pady=10)
        
        # ROUND FRAME
        self.roundFrame = ctk.CTkFrame(self, bg_color=Color.BLACK, fg_color=Color.BLACK)
        
        self.roundContainerFrame = ctk.CTkFrame(self.roundFrame, bg_color=Color.BLACK, fg_color=Color.BLACK)
        self.roundContainerFrame.pack(expand=True, side="top")
        
        self.roundCountLabel = ctk.CTkLabel(self.roundContainerFrame, text="", font=fonts.SMALL, wraplength=1500, text_color=Color.WHITE)
        self.roundCountLabel.pack(side="top")
        
        self.roundNameLabel = ctk.CTkLabel(self.roundContainerFrame, text="", font=fonts.LARGE, wraplength=1500, text_color=Color.WHITE)
        self.roundNameLabel.pack(expand=False, side="top")
        
        # TITLE FRAME
        self.titleFrame = ctk.CTkFrame(self, bg_color=Color.BLACK, fg_color=Color.BLACK)

        self.titleContainerFrame = ctk.CTkFrame(self.titleFrame, bg_color=Color.BLACK, fg_color=Color.BLACK)
        self.titleContainerFrame.pack(expand=True, side="top")

        self.titleLabel = ctk.CTkLabel(self.titleContainerFrame, text="", font=fonts.LARGE, wraplength=1500, text_color=Color.WHITE)
        self.titleLabel.pack(expand=True, side="top")
        
        self.subtitleLabel = ctk.CTkLabel(self.titleContainerFrame, text="", font=fonts.SMALL, wraplength=1500, text_color=Color.WHITE)
        self.subtitleLabel.pack(side="top")
        
        # SCOREBOARD FRAME
        self.scoreboardFrame = BigPictureScoreboard(self)
        
        # BUZZED LABEL
        self.buzzedLabel = ctk.CTkLabel(self, bg_color=Color.BLACK, fg_color=Color.BLACK, text="", font=fonts.LARGE, wraplength=1500, text_color=Color.WHITE)
        self.buzzedLabel.pack(padx=5, pady=15, side="bottom")
        
        self.title("Buzzer System Big Picture Display")
        
        self.fullscreen = False
        
    def updateRound(self, roundIndex, totalRounds, roundName):
        self.roundCountLabel.configure(text=f"Round {roundIndex} of {totalRounds}")
        self.roundNameLabel.configure(text=roundName)
        
    def updateTitle(self, title, subtitle):
        self.titleLabel.configure(text=title)
        self.subtitleLabel.configure(text=subtitle)
        
    def updateQuestion(self, question):
        self.questionLabel.configure(text=question)
        
    def toggleFullscreen(self):
        if self.fullscreen:
            self.deactivateFullscreen()
        else:
            self.activateFullscreen()
            
    def activateFullscreen(self):
        self.fullscreen = True

        self.overrideredirect(True)
        self.state("zoomed")

    def deactivateFullscreen(self):
        self.fullscreen = False
        
        self.overrideredirect(False)
        self.state("normal")
        
    def displayBlank(self):
        self.roundFrame.pack_forget()
        self.titleFrame.pack_forget()
        self.questionFrame.pack_forget()
        self.scoreboardFrame.pack_forget()
        
    def displayTitle(self):
        self.roundFrame.pack_forget()
        self.titleFrame.pack(expand=True, fill="both", side="top")
        self.questionFrame.pack_forget()
        self.scoreboardFrame.pack_forget()
        
    def displayRound(self):
        self.roundFrame.pack(expand=True, fill="both", side="top")
        self.titleFrame.pack_forget()
        self.questionFrame.pack_forget()
        self.scoreboardFrame.pack_forget()
        
    def displayQuestion(self):
        self.roundFrame.pack_forget()
        self.titleFrame.pack_forget()
        self.questionFrame.pack(expand=True, fill="both", side="top")
        self.scoreboardFrame.pack_forget()
        
    def displayScoreboard(self):
        self.roundFrame.pack_forget()
        self.titleFrame.pack_forget()
        self.questionFrame.pack_forget()
        self.scoreboardFrame.pack(expand=True, fill="both", side="top")
        
    def updateBuzzerAlias(self, aliasText, color=Color.WHITE):
        self.buzzedLabel.configure(text=aliasText, text_color=color)

class Selector(ctk.CTkToplevel):
    def __init__(self, master, options, callback, callbackArgs=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grab_set()
        
        self.__options = ctk.CTkOptionMenu(self, values=options)
        self.__options.set(options[0])
        self.__options.pack(fill="x", padx=5, pady=5)
        
        self.__callback = callback
        self.__callbackArgs = callbackArgs
        
        ctk.CTkButton(self, text="Submit Choice", command=self.submit).pack(fill="x", padx=5, pady=5)
            
    def submit(self):
        value = self.get()
        self.destroy()
        if self.__callbackArgs:
            self.__callback(value, *self.__callbackArgs)
        else:
            self.__callback(value)
        
    def get(self):
        return self.__options.get()

class TeamSetup(ctk.CTkScrollableFrame):
    def __init__(self, master, numBuzzers, setConfCallback, loadColorCallback, saveColorCallback, saveConfigCallback, loadConfigCallback, buzzerIdentifyCallback, **kwargs):
        super().__init__(master, **kwargs)
        
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=15)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        
        self.__numBuzzers = numBuzzers
        
        self.__setConfCallback = setConfCallback
        self.__loadColorCallback = loadColorCallback
        self.__saveColorCallback = saveColorCallback
        
        self.__buttonFrame = ctk.CTkFrame(self)
        self.__buttonFrame.grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky="EW")
        
        self.__buttonFrame.columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(self.__buttonFrame, text="Send Configuration to Device", command=self.setConfiguration).grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky="EW")
        ctk.CTkButton(self.__buttonFrame, text="Save to Database", command=lambda: saveConfigCallback(self.getConfig())).grid(row=1, column=0, padx=5, pady=5, sticky="EW")
        ctk.CTkButton(self.__buttonFrame, text="Load from Database", command=loadConfigCallback).grid(row=1, column=1, padx=5, pady=5, sticky="EW")        
        ctk.CTkButton(self.__buttonFrame, text="Stop Identify", command=lambda: buzzerIdentifyCallback(255)).grid(row=2, column=0, padx=5, pady=5, columnspan=2, sticky="EW")        
        
        self.__buzzerFrame = ctk.CTkFrame(self)
        self.__buzzerFrame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.__buzzerElements = []
        for i in range(self.__numBuzzers):
            newElement = BuzzerElement(self.__buzzerFrame, i, buzzerIdentifyCallback)
            newElement.grid(row=i//4, column=i%4, padx=5, pady=5)
            newElement.clearTeam()
            self.__buzzerElements.append(newElement)
        
        self.__teamFrame = ctk.CTkFrame(self)
        self.__teamFrame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.__teamElements = []
        
        self.__teamButtonFrame = ctk.CTkFrame(self.__teamFrame)
        self.__teamButtonFrame.pack(padx=5, pady=5, fill="x")
        
        ctk.CTkButton(self.__teamButtonFrame, text="New Team", command=self.newTeam).pack(padx=5, pady=5, fill="x")
        ctk.CTkButton(self.__teamButtonFrame, text="Save Teams", command=self.saveTeams).pack(padx=5, pady=5, fill="x")
        
        self.__teamDisplayFrame = ctk.CTkScrollableFrame(self.__teamFrame)
        self.__teamDisplayFrame.pack(padx=5, pady=5, expand=True, fill="both")
    
    def newTeam(self, name="", colors=None):
        newElement = TeamElement(self.__teamDisplayFrame, self.__loadColorCallback, self.__saveColorCallback)
        newElement.pack(padx=5, pady=5, fill="x")
        
        newElement.setName(name)
        if colors is not None:
            newElement.loadPalette(colors)
        
        self.__teamElements.append(newElement)
        
    def saveTeams(self):
        self.__teams = []
        teamNames = []
        
        for element in self.__teamElements:
            if not element.winfo_exists():
                continue
            
            if element.getName() == "" or element.getName() in teamNames:
                element.destroy()
                continue
            
            teamData = (element.getName(), element.getColors(), [])
            
            self.__teams.append(teamData)
            teamNames.append(element.getName())
            
        for element in self.__buzzerElements:
            element.setTeamList(teamNames)
        
    def setConfiguration(self):
        self.saveTeams()
        
        teamNames = [team[0] for team in self.__teams]
        
        for element in self.__buzzerElements:
            teamName = element.getTeam()
            if not element.getActive() or teamName == "CTkOptionMenu" or teamName not in teamNames:
                continue
            
            buzzerData = (element.index, element.alias)
            
            teamIndex = teamNames.index(teamName)
            self.__teams[teamIndex][2].append(buzzerData)
            
        self.__setConfCallback(self.__teams)
        
    def clear(self):
        for element in self.__teamElements:
            element.destroy()
        self.saveTeams()
        
        for element in self.__buzzerElements:
            element.clear()
        
    def getConfig(self):
        self.setConfiguration() # save to device before config is set to DB, so that we have the most up to date values
        
        teamNames = []
        buzzers = []
        for i, team in enumerate(self.__teams):
            teamNames.append(team[0])
            
            currentTeamBuzzers = [(buzzer[0], i, buzzer[1]) for buzzer in team[2]]
            buzzers.extend(currentTeamBuzzers)
        
        return teamNames, buzzers
    
    def loadConfig(self, config):
        self.clear()
        for team in config:
            self.newTeam(team[0], team[1])
            for buzzer in team[2]:
                self.__buzzerElements[buzzer[0]].setInfo(buzzer[1], True, team[0])
        
class TeamElement(ctk.CTkFrame):
    def __init__(self, master, loadColorCallback, saveColorCallback, **kwargs):
        super().__init__(master, **kwargs)
        
        self.__loadColorCallback = loadColorCallback
        self.__saveColorCallback = saveColorCallback
        
        self.__nameEntry = ctk.CTkEntry(self, placeholder_text="Alias")
        self.__nameEntry.pack(padx=5, pady=5, fill="x")
        
        self.__inactiveButton = ctk.CTkButton(self, text="Inactive Colour", command=self.setInactiveColor, fg_color="#444444")
        self.__inactiveButton.pack(padx=5, pady=5, fill="x")
        
        self.__waitingButton = ctk.CTkButton(self, text="Waiting Colour", command=self.setWaitingColor, fg_color="#660066")
        self.__waitingButton.pack(padx=5, pady=5, fill="x")
        
        self.__activeButton = ctk.CTkButton(self, text="Active Colour", command=self.setActiveColor, fg_color="#006600")
        self.__activeButton.pack(padx=5, pady=5, fill="x")
        
        self.__lockedButton = ctk.CTkButton(self, text="Locked Colour", command=self.setLockedColor, fg_color="#660000")
        self.__lockedButton.pack(padx=5, pady=5, fill="x")
        
        ctk.CTkButton(self, text="Load Colour Palette", command=lambda: self.__loadColorCallback(self)).pack(padx=5, pady=5, fill="x")
        ctk.CTkButton(self, text="Save Colour Palette", command=lambda: self.__saveColorCallback(self)).pack(padx=5, pady=5, fill="x")
        
    def getName(self):
        return self.__nameEntry.get()
    
    def loadPalette(self, palette):
        self.setInactiveColor(palette[0])
        self.setWaitingColor(palette[1])
        self.setActiveColor(palette[2])
        self.setLockedColor(palette[3])
        
    def setName(self, name):
        self.__nameEntry.delete(0, tk.END)
        self.__nameEntry.insert(0, name)
    
    def setInactiveColor(self, definedColor=None):
        if definedColor:
            self.__inactiveButton.configure(fg_color=definedColor)
        else:
            color = askcolor(title="Inactive Colour Chooser")
            if len(color) != 0:
                self.__inactiveButton.configure(fg_color=color[1])
            
    def setWaitingColor(self, definedColor=None):
        if definedColor:
            self.__waitingButton.configure(fg_color=definedColor)
        else:
            color = askcolor(title="Waiting Colour Chooser")
            if len(color) != 0:
                self.__waitingButton.configure(fg_color=color[1])
            
    def setActiveColor(self, definedColor=None):
        if definedColor:
            self.__activeButton.configure(fg_color=definedColor)
        else:
            color = askcolor(title="Active Colour Chooser")
            if len(color) != 0:
                self.__activeButton.configure(fg_color=color[1])
            
    def setLockedColor(self, definedColor=None):
        if definedColor:
            self.__lockedButton.configure(fg_color=definedColor)
        else:
            color = askcolor(title="Locked Colour Chooser")
            if len(color) != 0:
                self.__lockedButton.configure(fg_color=color[1])
            
    def getColors(self):
        return (self.__inactiveButton.cget("fg_color"), 
                self.__waitingButton.cget("fg_color"), 
                self.__activeButton.cget("fg_color"), 
                self.__lockedButton.cget("fg_color"))
        
class BuzzerElement(ctk.CTkFrame):
    def __init__(self, master, index, identifyCallback, **kwargs): 
        super().__init__(master, **kwargs)
        self.configure(fg_color="#ECECEC")
        
        self.__index = index
        
        self.__indexLabel = ctk.CTkLabel(self, text=f"Buzzer {self.__index}")
        self.__indexLabel.grid(row=0, column=0, padx=5, pady=5)
        
        self.__activeCheckbox = ctk.CTkCheckBox(self, text="")
        self.__activeCheckbox.grid(row=0, column=1, padx=5, pady=5)
        
        self.__aliasEntry = ctk.CTkEntry(self, placeholder_text="Alias")
        self.__aliasEntry.grid(row=1, column=0, padx=5, pady=5, columnspan=2, sticky="ew")
        
        self.__teamDropdown = ctk.CTkOptionMenu(self, values=[])
        self.__teamDropdown.grid(row=2, column=0, padx=5, pady=5, columnspan=2, sticky="ew")
        self.__teamDropdown.set("Select Team")
        
        ctk.CTkButton(self, text="Identify", command=lambda: identifyCallback(self.__index)).grid(row=3, column=0, padx=5, pady=5, columnspan=2, sticky="ew")
        
    def clearTeam(self):
        self.__teamDropdown.set("")
        
    def setTeamList(self, teams):
        self.__teamDropdown.configure(values=teams)
        
    def getTeam(self):
        return self.__teamDropdown.get()
    
    def getActive(self):
        return self.__activeCheckbox.get()
    
    def getInfo(self):
        return (self.__index, self.getActive(), self.getTeam(), self.alias)
    
    def setInfo(self, name, active, team):
        self.__aliasEntry.delete(0, tk.END)
        self.__aliasEntry.insert(0, name)
        
        if active:
            self.__activeCheckbox.select()
        else:
            self.__activeCheckbox.deselect()
            
        self.__teamDropdown.set(team)
    
    def clear(self):
        self.clearTeam()
        self.__activeCheckbox.deselect()
        self.__aliasEntry.delete(0, tk.END)
    
    @property
    def index(self):
        return self.__index
    
    @property
    def alias(self):
        return self.__aliasEntry.get()