from microbit import uart, button_a #type: ignore
import radio #type: ignore
import time

class BuzzerController:
    def __init__(self):
        uart.init(baudrate=9600)

        # setup the radio module
        radio.config(group=16, power=7)
        radio.on()

        self.__waitingForBuzz = False
        self.__activeID = None
        
        self.__lastCommand = ""

    def sendMsg(self, array):
        try:
            for i in range(3):
                radio.send_bytes(bytes(array))
                time.sleep_ms(10)
        except ValueError:
            print("ERROR: Byte value out of range.")

    def mainloop(self):
        serialData = ""
        while True:
            # check radio data for buzz
            radioData = radio.receive_bytes()
            if radioData:
                if int(radioData[0]) == 50:
                    if self.__waitingForBuzz:
                        if self.__activeID is None:
                            self.__waitingForBuzz = False
                            self.__activeID = int(radioData[1])
                            print("buzzed", str(radioData[1]))
                            
                            self.sendMsg([50, int(radioData[1])])
                        elif self.__activeID != int(radioData[1]):
                            self.sendMsg([55, int(radioData[1])])

            #! check for MACROS
            if button_a.is_pressed():
                if self.__lastCommand != "":
                    self.execute(self.__lastCommand)
                    time.sleep(0.1)

            # check serial data for command
            newByte = uart.read(1)
            if newByte is None:
                continue

            newChar = str(newByte, "utf-8")
            if newChar == "\n":
                self.__lastCommand = serialData
                self.execute(serialData)
                serialData = ""
            else:
                serialData += newChar

    def execute(self, serialData):
        print(serialData)
        commands = serialData.split(";")
        for command in commands:
            try:
                commandArray = list(map(int, command.split()))
            except ValueError:
                print("ERROR: Non integer value in command string.")
                continue
            
            self.sendMsg(commandArray)

            if commandArray[0] == 10 or commandArray[0] == 25 or commandArray[0] == 30 or commandArray[0] == 35:
                self.__waitingForBuzz = True
                self.__activeID = None
            elif commandArray[0] == 15 or commandArray[0] == 20 or commandArray[0] == 60 or commandArray[0] == 75 or commandArray[0] == 85:
                self.__waitingForBuzz = False

controller = BuzzerController()
controller.mainloop()
