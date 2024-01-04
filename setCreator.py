import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import sqlite3
from datetime import datetime
import pathlib
import shutil

class SetCreatorApp(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.title("Set Creator")
        
        self.db = sqlite3.connect("buzzer.db")
        self.cursor = self.db.cursor() #type: ignore
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=5, pady=5, expand=True, fill="both")
        
        self.tabview.add("Sets")
        
        self.tabview.add("Rounds")
        
        # QUESTION TAB
        self.tabview.add("Questions")
        qTab = QuestionTab(self.tabview.tab("Questions"), self.db, self.cursor)
        qTab.pack(padx=5, pady=5, expand=True, fill="both")
        
class QuestionTab(ctk.CTkFrame):
    def __init__(self, master, db, cursor, **kwargs):
        super().__init__(master, **kwargs)
        
        self.db = db
        self.cursor = cursor
        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)
        
        self.searchQuestionFrame = ctk.CTkScrollableFrame(self)
        self.searchQuestionFrame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # EDIT QUESTION FRAME
        self.activeID = None
        self.originalData = ["", "", "", ""]
        
        self.editQuestionFrame = ctk.CTkScrollableFrame(self)
        self.editQuestionFrame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.editIDLabel = ctk.CTkLabel(self.editQuestionFrame, text=f"ID: {self.activeID}")
        self.editIDLabel.pack(padx=5, pady=5, fill="x")
        
        self.editQuestionEntry = ctk.CTkTextbox(self.editQuestionFrame, height=50)
        self.editQuestionEntry.pack(padx=5, pady=5, fill="x")
        
        self.editAnswerEntry = ctk.CTkTextbox(self.editQuestionFrame, height=20)
        self.editAnswerEntry.pack(padx=5, pady=5, fill="x")
        
        self.editNotesEntry = ctk.CTkTextbox(self.editQuestionFrame, height=75)
        self.editNotesEntry.pack(padx=5, pady=5, fill="x")
        
        ctk.CTkButton(self.editQuestionFrame, text="Select Aid Path", command=self.selectAidPath).pack(padx=5, pady=5, fill="x")
        
        self.editAidLabel = ctk.CTkLabel(self.editQuestionFrame, text="No Aid Selected")
        self.editAidLabel.pack(padx=5, pady=5, fill="x")
        
        self.editSaveButton = ctk.CTkButton(self.editQuestionFrame, text="Add Question", command=self.saveChanges)
        self.editSaveButton.pack(padx=5, pady=5, fill="x")
        
        ctk.CTkButton(self.editQuestionFrame, text="Close without Saving", command=self.close).pack(padx=5, pady=5, fill="x")
        ctk.CTkButton(self.editQuestionFrame, text="Delete Question", command=self.delete, state="disabled").pack(padx=5, pady=5, fill="x")
        
    def selectAidPath(self):
        self.aidPath = filedialog.askopenfilename(title="Browse File")
        if self.aidPath:
            self.editAidLabel.configure(text=self.aidPath)
        else:
            self.editAidLabel.configure(text="No Aid Selected")
        
    def saveChanges(self):
        if not self.aidPath == self.originalData[3] and self.aidPath is not None:
            newFilename = datetime.now().strftime("%S%M%H%d%m%y")
            ext = pathlib.Path(self.aidPath).suffix
            
            newFile = "assets/" + newFilename + ext
            shutil.copyfile(self.aidPath, newFile)
        
        if self.activeID is not None:
            self.cursor.execute("UPDATE Question SET Question = ?, Answer = ?, Notes = ?, AidPath = ? WHERE ID = ?", (self.editQuestionEntry.get("1.0", tk.END), self.editAnswerEntry.get("1.0", tk.END), self.editNotesEntry.get("1.0", tk.END), self.activeID))
        else:
            self.cursor.execute("INSERT INTO Question (Question, Answer, Notes, AidPath) VALUES (?, ?, ?, ?)", (self.editQuestionEntry.get("1.0", tk.END), self.editAnswerEntry.get("1.0", tk.END), self.editNotesEntry.get("1.0", tk.END), self.aidPath))
        
    def close(self):
        pass
    
    def delete(self):
        pass
        
app = SetCreatorApp()
app.mainloop()