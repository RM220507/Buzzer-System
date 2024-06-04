import customtkinter as ctk
from PIL import Image
from customWidgets import BigPictureAidDisplay

NAVY = "#192841"
GOLD = "#EEB134"

EXTRA_LARGE = ctk.CTkFont("Bahnschrift Semibold", 140, "bold", "roman")
LARGE = ctk.CTkFont("Bahnschrift Semibold", 70, "bold", "roman")
SMALL = ctk.CTkFont("Bahnschrift Semibold", 36, "bold", "roman")

def createTitleFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=NAVY, fg_color=NAVY)
    
    titleContainerFrame = ctk.CTkFrame(frame, bg_color=NAVY, fg_color=NAVY)
    titleContainerFrame.pack(expand=True, side="top")
    
    titleLabel = ctk.CTkLabel(titleContainerFrame, text="", font=LARGE, wraplength=1000, text_color=GOLD)
    titleLabel.pack(expand=True, side="top")
    
    subtitleLabel = ctk.CTkLabel(titleContainerFrame, text="", font=SMALL, wraplength=1000, text_color=GOLD)
    subtitleLabel.pack(expand=True, side="top")
    
    image = ctk.CTkImage(Image.open("assets/house_crests.png"), size=(1640, 541))
    ctk.CTkLabel(titleContainerFrame, image=image, text="").pack(expand=True, side="top")
    
    parent.tagWidget("title", titleLabel)
    parent.tagWidget("subtitle", subtitleLabel)
    
    return frame

def createRoundFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=NAVY, fg_color=NAVY)
    
    roundContainerFrame = ctk.CTkFrame(frame, bg_color=NAVY, fg_color=NAVY)
    roundContainerFrame.pack(expand=True, side="top")
    
    roundCountLabel = ctk.CTkLabel(roundContainerFrame, text="", font=SMALL, wraplength=1000, text_color=GOLD)
    roundCountLabel.pack(side="top")
    
    roundNameLabel = ctk.CTkLabel(roundContainerFrame, text="", font=LARGE, wraplength=1000, text_color=GOLD)
    roundNameLabel.pack(expand=False, side="top")
    
    parent.tagWidget("roundCount", roundCountLabel)
    parent.tagWidget("roundName", roundNameLabel)
    
    return frame

def createQuestionFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=NAVY, fg_color=NAVY)
    
    label = ctk.CTkLabel(frame, text="", font=LARGE, wraplength=1000, text_color=GOLD)
    label.pack(expand=True, side="top")
    
    aidDisplay = BigPictureAidDisplay(frame)
    aidDisplay.pack(expand=True, fill="both", padx=10, pady=10)
    
    parent.tagWidget("question", label)
    parent.tagWidget("questionAid", aidDisplay)
    
    return frame

def createScoreboardFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=NAVY, fg_color=NAVY)
    
    ctk.CTkLabel(frame, text="Scoreboard", text_color=GOLD, font=EXTRA_LARGE).pack(fill="x", padx=10, pady=10)
    
    scoreboardFrame = ctk.CTkScrollableFrame(frame, bg_color=NAVY, fg_color=NAVY)
    scoreboardFrame.pack(expand=True, fill="both", padx=10, pady=10)
    
    parent.tagWidget("scoreboard", scoreboardFrame)
    
    return frame

def createBlankFrame(parent):
    frame = ctk.CTkFrame(parent, bg_color=NAVY, fg_color=NAVY)
    return frame

def createScoreboardItem(parent, teamName, score, color):
    frame = ctk.CTkFrame(parent)
    
    ctk.CTkLabel(frame, text=teamName, font=EXTRA_LARGE, text_color=color).grid(row=0, column=0, sticky="W")
    ctk.CTkLabel(frame, text=str(score), font=EXTRA_LARGE, text_color=color).grid(row=0, column=1, sticky="E")
    
    frame.pack(padx=5, pady=5)