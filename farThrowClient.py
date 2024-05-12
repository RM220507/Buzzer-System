import socketio as sio
from time import sleep
import serial
import serial.tools.list_ports as list_ports

client = sio.Client()

class SerialController:
    def __init__(self):        
        self.attemptConnection()

    def attemptConnection(self):
        self.__port = self.findCOMport(516, 3368, 9600)
        print(self.__port)
        if not self.__port.is_open:
            self.raiseException()

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
        return self.__port.in_waiting > 0

    def getLine(self):
        return self.__port.readline().decode("utf-8")

    def single(self, command):
        print("Received SINGLE: " + command)
        try:
            self.__port.write(bytes((command + "\n"), "utf-8"))
            return True
        except Exception as e:
            print(f"An error occured. Try restarting the application. {e}")
            input("Press ENTER to ignore this error. ")
            
    def multi(self, commands):
        commandString = ";".join(commands)
        print("Received MULTI: " + commandString)
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
                if not self.single(smallCommand):
                    break
                sleep(0.5)
        else:
            self.single(commandString)

    def raiseException(self):
        input("No controller micro:bit was detected. Press ENTER to retry. ")
        self.attemptConnection()

    def run(self):
        while True:
            #self.single("12 34 123")
            try:
                if self.checkBuffer():
                    data = self.getLine()
                    self.readCallback(data)
            except:
                self.raiseException()
                
    def readCallback(self, data):
        print("TRANSMIT from SERIAL: " + data)
        client.emit("receive", data)

@client.event
def connect():
    print("Connected to Server.")
    
@client.event
def disconnect():
    print("Disconnected from Server.")

serialController = SerialController()

client.on("single", serialController.single)
client.on("multi", serialController.multi)

SERVER_HOST = input("Input the hostname to connect to: ")
SERVER_PORT = input("Input port: ")

client.connect(f"http://{SERVER_HOST}:{SERVER_PORT}")
serialController.run()