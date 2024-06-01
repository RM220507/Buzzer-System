import customtkinter as ctk
from customWidgets import BigPictureAidDisplay, BigPictureScoreboard

print("Imported")

BLACK = "#000000"
WHITE = "#FFFFFF"

EXTRA_LARGE = ctk.CTkFont("Bahnschrift Semibold", 140, "bold", "roman")
LARGE = ctk.CTkFont("Bahnschrift Semibold", 65, "bold", "roman")
SMALL = ctk.CTkFont("Bahnschrift Semibold", 36, "bold", "roman")

def createTitleFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=BLACK, fg_color=BLACK)
    
    titleContainerFrame = ctk.CTkFrame(frame, bg_color=BLACK, fg_color=BLACK)
    titleContainerFrame.pack(expand=True, side="top")
    
    titleLabel = ctk.CTkLabel(titleContainerFrame, text="", font=LARGE, wraplength=1000, text_color=WHITE)
    titleLabel.pack(expand=True, side="top")
    
    subtitleLabel = ctk.CTkLabel(titleContainerFrame, text="", font=SMALL, wraplength=1000, text_color=WHITE)
    subtitleLabel.pack(expand=True, side="top")
    
    parent.tagWidget("title", titleLabel)
    parent.tagWidget("subtitle", subtitleLabel)
    
    return frame

def createRoundFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=BLACK, fg_color=BLACK)
    
    roundContainerFrame = ctk.CTkFrame(frame, bg_color=BLACK, fg_color=BLACK)
    roundContainerFrame.pack(expand=True, side="top")
    
    roundCountLabel = ctk.CTkLabel(roundContainerFrame, text="", font=SMALL, wraplength=1000, text_color=WHITE)
    roundCountLabel.pack(side="top")
    
    roundNameLabel = ctk.CTkLabel(roundContainerFrame, text="", font=LARGE, wraplength=1000, text_color=WHITE)
    roundNameLabel.pack(expand=False, side="top")
    
    parent.tagWidget("roundCount", roundCountLabel)
    parent.tagWidget("roundName", roundNameLabel)
    
    return frame

def createQuestionFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=BLACK, fg_color=BLACK)
    
    label = ctk.CTkLabel(frame, text="", font=LARGE, wraplength=1000, text_color=WHITE)
    label.pack(expand=True, side="top")
    
    aidDisplay = BigPictureAidDisplay(frame)
    aidDisplay.pack(expand=True, fill="both", padx=10, pady=10)
    
    parent.tagWidget("question", label)
    parent.tagWidget("questionAid", aidDisplay)
    
    return frame

def createScoreboardFrame(parent):
    frame = ctk.CTkScrollableFrame(parent)
    
    parent.tagWidget("scoreboard", frame)
    
    return frame

def createBlankFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=BLACK, fg_color=BLACK)
    return frame

def createScoreboardItem(parent, teamName, score, color):
    frame = ctk.CTkFrame(parent)
    
    ctk.CTkLabel(frame, text=teamName, font=EXTRA_LARGE, text_color=color).grid(row=0, column=0, sticky="W")
    ctk.CTkLabel(frame, text=str(score), font=EXTRA_LARGE, text_color=color).grid(row=0, column=1, sticky="E")
    
    frame.pack(padx=5, pady=5)