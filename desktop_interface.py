import customtkinter as ctk

class QuestionInfoPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.rowconfigure((0, 1), weight=1)
        self.columnconfigure(())

class Interface(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__()
        
        self.title("Buzzer System")
        

app = Interface()
app.mainloop()