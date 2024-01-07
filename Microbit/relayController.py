from microbit import uart, display #type: ignore
import radio #type: ignore

class BuzzerController:
    def __init__(self):
        uart.init(baudrate=9600)

        # setup the radio module
        radio.config(group=16, power=7)
        radio.on()

        self.__waitingForBuzz = False
    
    def sendMsg(self, array):
        radio.send_bytes(bytes(array))
    
    def mainloop(self):
        serialData = ""
        while True:
            # check radio data for buzz
            radioData = radio.receive_bytes()
            if radioData:
                if int(radioData[0]) == 50:
                    if self.__waitingForBuzz:
                        self.__waitingForBuzz = False
                        print("buzzed", str(radioData[1]))
                    else:
                        self.sendMsg([55, radioData[1]])

            #! check for MACROS

            # check serial data for command
            newByte = uart.read(1)
            if newByte is None:
                continue
            
            newChar = str(newByte, "UTF-8")
            if newChar == "\n":
                print(serialData)
                self.execute(serialData)
                serialData = ""
            else:
                serialData += newChar
                
    def execute(self, serialData):
        commands = serialData.split(";")
        for command in commands:
            commandArray = list(map(int, serialData.split()))
            self.sendMsg(commandArray)
            
            if command[0] == 10 or command[0] == 25 or command[0] == 30 or command[0] == 35:
                self.__waitingForBuzz = True
            elif command[0] == 15 or command[0] == 20 or command[0] == 60 or command[0] == 75:
                self.__waitingForBuzz = False
                
controller = BuzzerController()
controller.mainloop()