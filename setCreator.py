import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import sqlite3
from datetime import datetime
import pathlib
import shutil
import math

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
        
        self.searchQuestionFrame = ctk.CTkFrame(self)
        self.searchQuestionFrame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.searchPaginationFrame = ctk.CTkFrame(self.searchQuestionFrame)
        self.searchPaginationFrame.pack(padx=5, pady=5, fill="x")
        
        self.SEARCH_PAGE_SIZE = 15
        
        ctk.CTkButton(self.searchPaginationFrame, text="<<", command=self.searchFirstPage).pack(padx=5, pady=5, side="left", fill="x")
        ctk.CTkButton(self.searchPaginationFrame, text="<", command=self.searchPreviousPage).pack(padx=5, pady=5, side="left", fill="x")
        
        self.searchPageLabel = ctk.CTkLabel(self.searchPaginationFrame, text="0 of 0")
        self.searchPageLabel.pack(padx=5, pady=5, side="left", fill="x")
        
        ctk.CTkButton(self.searchPaginationFrame, text=">", command=self.searchNextPage).pack(padx=5, pady=5, side="left", fill="x")
        ctk.CTkButton(self.searchPaginationFrame, text=">>", command=self.searchLastPage).pack(padx=5, pady=5, side="left", fill="x")
        
        self.searchResultsFrame = ctk.CTkScrollableFrame(self.searchQuestionFrame)
        self.searchResultsFrame.pack(padx=5, pady=5, fill="both", expand=True)
        
        self.searchFirstPage()
        
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
        self.editDeleteButton = ctk.CTkButton(self.editQuestionFrame, text="Delete Question", command=self.delete, state="disabled")
        self.editDeleteButton.pack(padx=5, pady=5, fill="x")
        
    def searchFirstPage(self):
        questions = self.getQuestions()
        self.searchPageNumber = 0
        self.searchDisplayResults(questions)
    
    def searchPreviousPage(self):
        questions = self.getQuestions()
        if self.searchPageNumber > 0:
            self.searchPageNumber -= 1
            self.searchDisplayResults(questions)
    
    def searchNextPage(self):
        questions = self.getQuestions()
        if self.searchPageNumber < (math.ceil(len(questions) / self.SEARCH_PAGE_SIZE) - 1):
            self.searchPageNumber += 1
            self.searchDisplayResults(questions)
    
    def searchLastPage(self):
        questions = self.getQuestions()
        self.searchPageNumber = math.ceil(len(questions) / self.SEARCH_PAGE_SIZE) - 1
        self.searchDisplayResults(questions)
    
    def searchDisplayResults(self, questions):
        for result in self.searchResultsFrame.winfo_children():
            result.destroy()
            
        firstIndex = self.searchPageNumber * self.SEARCH_PAGE_SIZE
        lastIndex = firstIndex + self.SEARCH_PAGE_SIZE
        
        results = questions[firstIndex:lastIndex + 1]
        for result in results:
            ctk.CTkButton(self.searchResultsFrame, text=f"{result[0]} - {result[1]}", command=lambda ix=result[0]: self.open(ix)).pack(padx=5, pady=5, fill="x")

        self.searchPageLabel.configure(text=f"{self.searchPageNumber + 1} of {math.ceil(len(questions) / self.SEARCH_PAGE_SIZE)}")
    
    def open(self, index):
        self.cursor.execute("SELECT * FROM Question WHERE ID = ?", (index,))
        result = self.cursor.fetchall()
        if len(result) == 0: return
        
        self.close()
        
        self.originalData = result[0]
        self.activeID = index
        
        self.editIDLabel.configure(text=f"ID: {index}")
        
        self.editQuestionEntry.insert("1.0", self.originalData[1])
        self.editAnswerEntry.insert("1.0", self.originalData[2])
        self.editNotesEntry.insert("1.0", self.originalData[3])
        
        if self.originalData[4]:
            self.editAidLabel.configure(text=self.originalData[4])
    
    def getQuestions(self):
        self.cursor.execute("SELECT ID, Question FROM Question")
        return self.cursor.fetchall()
        
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
        
        self.db.commit()
        self.close()
        
    def close(self):
        self.activeID = None
        self.originalData = ["", "", "", ""]
        
        self.editIDLabel.configure(text="ID: None")
        
        self.editQuestionEntry.delete("1.0", tk.END)
        self.editAnswerEntry.delete("1.0", tk.END)
        self.editNotesEntry.delete("1.0", tk.END)
        
        self.editAidLabel.configure(text="No Aid Selected")
        
        self.editSaveButton.configure(text="Add Question")
        self.editDeleteButton.configure(state="disabled")
    
    def delete(self):
        if self.activeID is not None:
            self.cursor.execute("DELETE FROM Question WHERE ID = ?", (self.activeID,))
            self.db.commit()
            self.close()
        
app = SetCreatorApp()
app.mainloop()