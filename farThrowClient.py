import socketio as sio
from time import sleep
import serial
import serial.tools.list_ports as list_ports
from serial import serialutil
import logging

logging.basicConfig(format="%(levelname)s - %(message)s",level=logging.INFO)

client = sio.Client()

class SerialController:
    def __init__(self):
        self.attemptConnection()

    def attemptConnection(self):
        self.__port = self.findCOMport(516, 3368, 9600)
        if not self.__port.is_open:
            return False
        else:
            logging.info("Connected to Micro:bit.")
            return True

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
            
    def raiseException(self):
        logging.error("Disconnected from Micro:bit.")
        while not self.attemptConnection():
            logging.info("Attempting to connect to Micro:bit.")
            sleep(2)

    def run(self):
        while True:
            try:
                #if self.__port.is_open:
                if self.checkBuffer():
                    data = self.getLine()
                    self.readCallback(data)
                #else:
                #    self.raiseException()
            except Exception as e:
                self.raiseException()
                print(e)
                
    def readCallback(self, data):
        logging.debug("TRANSMIT from SERIAL: " + data)
        client.emit("receive", data)

@client.event
def connect():
    logging.info("Connected to Server.")
    
@client.event
def disconnect():
    logging.error("Disconnected from Server.")
    
def receiveUpdate(data):
    logging.debug("Receiving update.")
    
    print("------------------------------------------------")
    print("CURRENT QUESTION")
    print(f"Question: {data['questionData'][0]}")
    print(f"Answer: {data['questionData'][1]}")
    print(f"Notes: {data['questionData'][2]}")
    print(f"Points: CORRECT - {data['questionData'][3]}; INCORRECT - {data['questionData'][4]}")
    print(f"Current Round: {data['roundData'][1]} ({data['roundData'][0]} of {data['numRounds']})")
    print()
    print("BIG PICTURE DISPLAY")
    print(f"Displaying: {data['currentDisplay']}")
    print()
    print("CURRENT SCORES")
    for score in data["scores"]:
        print(f"{score[0]} - {score[1]}")
    print("END OF UPDATE")
    print("------------------------------------------------")
    
def receiveBuzz(data):
    logging.debug("Receiving buzz notification.")
    print(f"BUZZED: {data[0]} - {data[1]}")

serialController = SerialController()

client.on("single", serialController.single)
client.on("multi", serialController.multi)
client.on("update", receiveUpdate)
client.on("buzz", receiveBuzz)

SERVER_HOST = input("Input the hostname to connect to: ")
SERVER_PORT = input("Input port: ")

client.connect(f"http://{SERVER_HOST}:{SERVER_PORT}")
serialController.run()