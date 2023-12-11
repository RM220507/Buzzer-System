import customtkinter as ctk
from tkinter.colorchooser import askcolor

class TeamSetup(ctk.CTkScrollableFrame):
    def __init__(self, master, numBuzzers, setConfCallback, **kwargs):
        super().__init__(master, **kwargs)
        
        self.rowconfigure(1, weight=15)
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=1)
        
        self.__numBuzzers = numBuzzers
        self.__setConfCallback = setConfCallback
        
        self.__buttonFrame = ctk.CTkFrame(self)
        self.__buttonFrame.grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky="EW")
        
        self.__buttonFrame.columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(self.__buttonFrame, text="Send Configuration to Device", command=self.setConfiguration).grid(row=0, column=0, padx=5, pady=5, columnspan=2, sticky="EW")
        ctk.CTkButton(self.__buttonFrame, text="Save to Database", command=lambda: print("Save")).grid(row=1, column=0, padx=5, pady=5, sticky="EW")
        ctk.CTkButton(self.__buttonFrame, text="Load from Database", command=lambda: print("Load")).grid(row=1, column=1, padx=5, pady=5, sticky="EW")        
        
        self.__buzzerFrame = ctk.CTkFrame(self)
        self.__buzzerFrame.grid(row=1, column=0, padx=5, pady=5, sticky="NSEW")
        
        self.__buzzerElements = []
        for i in range(self.__numBuzzers):
            newElement = BuzzerElement(self.__buzzerFrame, i)
            newElement.grid(row=i//4, column=i%4, padx=5, pady=5)
            self.__buzzerElements.append(newElement)
        
        self.__teamFrame = ctk.CTkFrame(self)
        self.__teamFrame.grid(row=1, column=1, padx=5, pady=5, sticky="NSEW")
        
        self.__teamElements = []
        
        self.__teamButtonFrame = ctk.CTkFrame(self.__teamFrame)
        self.__teamButtonFrame.pack(padx=5, pady=5, fill="x")
        
        ctk.CTkButton(self.__teamButtonFrame, text="New Team", command=self.newBlankTeam).pack(padx=5, pady=5, fill="x")
        ctk.CTkButton(self.__teamButtonFrame, text="Save Teams", command=self.saveTeams).pack(padx=5, pady=5, fill="x")
        
        self.__teamDisplayFrame = ctk.CTkScrollableFrame(self.__teamFrame)
        self.__teamDisplayFrame.pack(padx=5, pady=5, expand=True, fill="both")
    
    def newBlankTeam(self):
        newElement = TeamElement(self.__teamDisplayFrame)
        newElement.pack(padx=5, pady=5, fill="x")
        
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
        
class TeamElement(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
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
        
        ctk.CTkButton(self, text="Load Colour Palette").pack(padx=5, pady=5, fill="x")
        ctk.CTkButton(self, text="Save Colour Palette").pack(padx=5, pady=5, fill="x")
        
    def getName(self):
        return self.__nameEntry.get()
    
    def setInactiveColor(self):
        color = askcolor(title="Inactive Colour Chooser")
        if color:
            self.__inactiveButton.configure(fg_color=color[1])
            
    def setWaitingColor(self):
        color = askcolor(title="Waiting Colour Chooser")
        if color:
            self.__waitingButton.configure(fg_color=color[1])
            
    def setActiveColor(self):
        color = askcolor(title="Active Colour Chooser")
        if color:
            self.__activeButton.configure(fg_color=color[1])
            
    def setLockedColor(self):
        color = askcolor(title="Locked Colour Chooser")
        if color:
            self.__lockedButton.configure(fg_color=color[1])
            
    def getColors(self):
        return (self.__inactiveButton.cget("fg_color"), 
                self.__waitingButton.cget("fg_color"), 
                self.__activeButton.cget("fg_color"), 
                self.__lockedButton.cget("fg_color"))
        
class BuzzerElement(ctk.CTkFrame):
    def __init__(self, master, index, **kwargs): 
        super().__init__(master, **kwargs)
        self.configure(fg_color="#ECECEC")
        
        self.__index = index
        
        self.__indexLabel = ctk.CTkLabel(self, text=f"Buzzer {self.__index}")
        self.__indexLabel.grid(row=0, column=0, padx=5, pady=5)
        
        self.__activeCheckbox = ctk.CTkCheckBox(self, text="")
        self.__activeCheckbox.grid(row=0, column=1, padx=5, pady=5)
        
        self.__aliasEntry = ctk.CTkEntry(self, placeholder_text="Alias")
        self.__aliasEntry.grid(row=1, column=0, padx=5, pady=5, columnspan=2)
        
        self.__teamDropdown = ctk.CTkOptionMenu(self, values=[])
        self.__teamDropdown.grid(row=2, column=0, padx=5, pady=5, columnspan=2)
        
    def setTeamList(self, teams):
        self.__teamDropdown.configure(values=teams)
        
    def getTeam(self):
        return self.__teamDropdown.get()
    
    def getActive(self):
        return self.__activeCheckbox.get()
    
    @property
    def index(self):
        return self.__index
    
    @property
    def alias(self):
        return self.__aliasEntry.get()