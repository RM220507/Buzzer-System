import socketio as sio
from time import sleep
import serial
import serial.tools.list_ports as list_ports
from serial import serialutil
import logging
import customtkinter as ctk
from os import path
from PIL import ImageTk

logging.basicConfig(format="%(levelname)s - %(message)s", level=logging.INFO)

RED = "#FF0000"
GREEN = "#00AA00"
BLUE = "#0000FF"
BLACK = "#000000"

class SerialController:
    def attemptConnection(self):
        self.__port = self.findCOMport(516, 3368, 9600)
        return self.__port.is_open

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
        try:
            return self.__port.in_waiting > 0
        except serialutil.SerialException:
            self.raiseException()       

    def getLine(self):
        return self.__port.readline().decode("utf-8")

    def write(self, command):
        try:
            self.__port.write(bytes((command + "\n"), "utf-8"))
            return True
        except Exception as e:
            print(f"An error occured. Try restarting the application. {e}")
            input("Press ENTER to ignore this error. ")

    def single(self, command):
        logging.debug("Received SINGLE: " + command)
        self.write(command)
        
    def multi(self, commands):
        commandString = ";".join(commands)
        logging.debug("Received MULTI: " + commandString)
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
                if not self.write(smallCommand):
                    break
                sleep(0.5)
        else:
            self.write(commandString)

    def checkInput(self):
        try:
            if self.checkBuffer():
                data = self.getLine()
                return data
        except Exception:
            return 400

class FarThrowClient(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.__client = sio.Client()
        
        self.__serialController = SerialController()
        
        self.__client.on("connect", self.connected)
        self.__client.on("disconnect", self.disconnected)
        self.__client.on("single", self.__serialController.single)
        self.__client.on("multi", self.__serialController.multi)
        self.__client.on("update", self.receiveUpdate)
        self.__client.on("buzz", self.receiveBuzz)
        self.__client.on("image", self.receiveImage)
        self.__client.on("bigPicture", self.receiveBigPicture)
        self.__client.on("scores", self.receiveScores)
        
        self.iconpath = ImageTk.PhotoImage(file=path.join("assets", "icon.png"))
        self.wm_iconbitmap()
        self.iconphoto(False, self.iconpath)
        
        self.title("Buzzer System - Far Throw Client")
        
        statusBar = ctk.CTkFrame(self)
        statusBar.columnconfigure((0, 1), weight=1)
        
        self.__serverConnectedLabel = ctk.CTkLabel(statusBar, text="Not Connected to Server", text_color=RED)
        self.__serverConnectedLabel.grid(row=0, column=0, padx=5, pady=5, sticky="EW")
        
        self.__microbitConnectedLabel = ctk.CTkLabel(statusBar, text="Not Connected to Micro:bit", text_color=RED)
        self.__microbitConnectedLabel.grid(row=0, column=1, padx=5, pady=5, sticky="EW")
        
        statusBar.pack(padx=5, pady=5, fill="x")
        
        updateFrame = ctk.CTkFrame(self)
        
        ctk.CTkLabel(updateFrame, text="Question:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
        self.__questionLabel = ctk.CTkLabel(updateFrame, text="")
        self.__questionLabel.grid(row=0, column=1, padx=5, pady=5, sticky="EW")
        
        ctk.CTkLabel(updateFrame, text="Answer:").grid(row=1, column=0, padx=5, pady=5, sticky="W")
        self.__answerLabel = ctk.CTkLabel(updateFrame, text="")
        self.__answerLabel.grid(row=1, column=1, padx=5, pady=5, sticky="EW")
        
        ctk.CTkLabel(updateFrame, text="Notes:").grid(row=2, column=0, padx=5, pady=5, sticky="W")
        self.__notesLabel = ctk.CTkLabel(updateFrame, text="")
        self.__notesLabel.grid(row=2, column=1, padx=5, pady=5, sticky="EW")
    
        ctk.CTkLabel(updateFrame, text="Points:").grid(row=3, column=0, padx=5, pady=5, sticky="W")
        self.__pointsLabel = ctk.CTkLabel(updateFrame, text="")
        self.__pointsLabel.grid(row=3, column=1, padx=5, pady=5, sticky="EW")
    
        ctk.CTkLabel(updateFrame, text="Round:").grid(row=4, column=0, padx=5, pady=5, sticky="W")
        self.__roundLabel = ctk.CTkLabel(updateFrame, text="")
        self.__roundLabel.grid(row=4, column=1, padx=5, pady=5, sticky="EW")
    
        ctk.CTkLabel(updateFrame, text="Big Picture Display:").grid(row=5, column=0, padx=5, pady=5, sticky="W")
        self.__displayLabel = ctk.CTkLabel(updateFrame, text="")
        self.__displayLabel.grid(row=5, column=1, padx=5, pady=5, sticky="EW")
        
        ctk.CTkLabel(updateFrame, text="Buzzer Alias:").grid(row=6, column=0, padx=5, pady=5, sticky="W")
        self.__buzzerLabel = ctk.CTkLabel(updateFrame, text="")
        self.__buzzerLabel.grid(row=6, column=1, padx=5, pady=5, sticky="EW")
    
        updateFrame.pack(padx=5, pady=5, fill="both")
        
        self.__scoreFrame = ctk.CTkFrame(self)
        self.__scoreFrame.pack(padx=5, pady=5, fill="x")
    
    def connected(self):
        self.__serverConnectedLabel.configure(text="Connected to Server", text_color=GREEN)
        
    def disconnected(self):
        try:
            self.__serverConnectedLabel.configure(text="Not Connected to Server", text_color=RED)
        except:
            return
            
    def attemptMicrobitConnection(self):
        logging.debug("Attempting Micro:bit connection.")
        self.__microbitConnectedLabel.configure(text="Not Connected to Micro:bit", text_color=RED)
        
        result = self.__serialController.attemptConnection()
        if result:
            logging.debug("Connected to Micro:bit.")
            self.__microbitConnectedLabel.configure(text="Connected to Micro:bit", text_color=GREEN)
            
            self.checkSerialData()
        else:
            self.after(2000, self.attemptMicrobitConnection)
    
    def checkSerialData(self):        
        result = self.__serialController.checkInput()
        if result is not None and result != 400:
            self.sendSerialData(result)
            
        if result != 400:
            self.after(10, self.checkSerialData)
        else:
            self.attemptMicrobitConnection()
    
    def sendSerialData(self, data):
        logging.debug("TRANSMIT from SERIAL: " + data)
        self.__client.emit("receive", data)
    
    def resetBuzzerColor(self):
        self.__buzzerLabel.configure(text_color=BLUE)
    
    def resetUpdateColor(self):
        self.__questionLabel.configure(text_color=BLACK)
        self.__answerLabel.configure(text_color=BLACK)
        self.__notesLabel.configure(text_color=BLACK)
        self.__pointsLabel.configure(text_color=BLACK)
        self.__roundLabel.configure(text_color=BLACK)
        self.__displayLabel.configure(text_color=BLACK)
    
    def resetBigPictureColor(self):
        self.__displayLabel.configure(text_color=BLACK)
    
    def resetScoresColor(self):
        for child in self.__scoreFrame.winfo_children():
            child.configure(text_color=BLACK)
    
    def receiveBigPicture(self, data):
        logging.debug("Receiving Big Picture Display status.")
        self.__displayLabel.configure(text=data, text_color=BLUE)
        
        self.after(1000, self.resetBigPictureColor)
    
    def receiveUpdate(self, data):
        logging.debug("Receiving update.")
        
        self.__questionLabel.configure(text=data["questionData"][0], text_color=BLUE)
        self.__answerLabel.configure(text=data["questionData"][1], text_color=BLUE)
        self.__notesLabel.configure(text=data["questionData"][2], text_color=BLUE)
        self.__pointsLabel.configure(text=f"CORRECT - {data['questionData'][3]}; INCORRECT - {data['questionData'][4]}", text_color=BLUE)
        self.__roundLabel.configure(text=f"{data['roundData'][1]} ({data['roundData'][0]} of {data['numRounds']})", text_color=BLUE)
        self.__displayLabel.configure(text=data["currentDisplay"], text_color=BLUE)
        
        self.after(1000, self.resetUpdateColor)
        
        self.receiveScores(data["scores"])
        
    def receiveScores(self, scores):
        for child in self.__scoreFrame.winfo_children():
            child.destroy()
        
        for score in scores:
            teamLabel = ctk.CTkLabel(self.__scoreFrame, text=f"{score[0].upper()} - {score[1]}", text_color=BLUE)
            teamLabel.pack(padx=5, pady=5)
            
        self.after(1000, self.resetScoresColor)
        
    def receiveBuzz(self, data):
        logging.debug("Receiving buzz notification.")
        
        if data[0] == "" and data[1] == "":
            self.__buzzerLabel.configure(text="")
        else:
            self.__buzzerLabel.configure(text=f"{data[0]} - {data[1]}", text_color=RED)
        
        self.after(1000, self.resetBuzzerColor)
        
    def receiveImage(self, data):
        return
    
    def run(self):
        hostDialog = ctk.CTkInputDialog(title="Enter Host Socket", text="Enter the socket address to connect to:")
        
        self.__client.connect(f"http://{hostDialog.get_input()}")
        
        try:
            self.after(100, self.attemptMicrobitConnection)
            self.mainloop()
        finally:
            self.__client.disconnect()

farThrowClient = FarThrowClient()
farThrowClient.run()