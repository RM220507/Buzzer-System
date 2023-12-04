import serial
import time

serialPort = serial.Serial(port="COM9", baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)

serialPort.write(b"Hello")