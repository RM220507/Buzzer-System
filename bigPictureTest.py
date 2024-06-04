import customtkinter as ctk
from glob import glob
from os import path
from PIL import ImageTk
from customWidgets import createPopOutBigPictureControl, BigPicture, Selector

def loadLayoutPrompt():
    availableFiles = glob("assets/bigPictureLayouts/*.py")
    availableFiles = [path.splitext(path.basename(file))[0] for file in availableFiles]
    availableFiles.append("DEFAULT")
            
    Selector(app, availableFiles, loadLayout)

def showQuestion():
    if not bigPicture.winfo_exists():
        openBigPicture()
        
    bigPicture.displayQuestion()
    
def showRound():
    if not bigPicture.winfo_exists():
        openBigPicture()
        
    bigPicture.displayRound()
    
def showScoreboard():
    if not bigPicture.winfo_exists():
        openBigPicture()
        
    bigPicture.displayScoreboard()
    
def showTitle():
    if not bigPicture.winfo_exists():
        openBigPicture()
        
    bigPicture.displayTitle()
    
def showBlank():
    if not bigPicture.winfo_exists():
        openBigPicture()
        
    bigPicture.displayBlank()
    
def loadLayout(name):
    global layoutName
    
    layoutName = name
    
    bigPicture.loadLayout(name)
    
    bigPicture.updateBuzzerAlias("Placeholder", "Buzzer")
    bigPicture.updateQuestion("Placeholder Question Goes Here?")
    bigPicture.updateRound(1, 10, "Placeholder Round")
    bigPicture.updateTitle("Placeholder Title", "Placeholder Subtitle")

def openBigPicture():
    global bigPicture
    
    bigPicture = BigPicture(app)

    testConfig = {
        "buzzerData" : {
            "display" : True,
            "teamName" : True,
            "buzzerName" : True
        },
        "seqActions" : {}
    }
    bigPicture.setConfig(testConfig)
    loadLayout(layoutName)
    
app = ctk.CTk()
app.title("Buzzer System - Big Picture Tester")

iconpath = ImageTk.PhotoImage(file=path.join("assets", "icon.png"))
app.wm_iconbitmap()
app.iconphoto(False, iconpath)

controlFrame = createPopOutBigPictureControl(
    app,
    showQuestion,
    showRound,
    showScoreboard,
    showBlank,
    showTitle
)
ctk.CTkButton(app, text="Load Layout", command=loadLayoutPrompt).pack(padx=5, pady=5, fill="x")
controlFrame.pack(padx=5, pady=5, expand=True, fill="both")

layoutName = "DEFAULT"
openBigPicture()

app.mainloop()