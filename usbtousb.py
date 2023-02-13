import json
import os
import serial
import sys
from dotenv import load_dotenv
from time import sleep
from enum import auto
from enum import Enum
from key_mapping import keymap

class KeyAction(Enum):
    TAP = auto()
    RELEASE = auto()
    PRESS = auto()

class UsbToUsb:
    # the settings used to connect here, are those required by the USBtoUSB (Hagstrom Electronics product) hardware
    baudrate = 19200
    bytesize = 8
    parity = serial.PARITY_NONE
    stopbits = serial.STOPBITS_ONE

    def __init__(self):
        load_dotenv() # load .env variables

        # connect to the USBtoUSB com port
        port_name = os.environ.get('PORT_NAME');
        self.com = serial.Serial(port_name, self.baudrate, self.bytesize, self.parity, self.stopbits)

    def sendByte(self, value: int):
        self.com.write((value).to_bytes(1, 'big', signed = False))

    def keyAction(self, key: str, action: KeyAction):
        key_code_press = keymap[key][0] # code to press down the key
        key_code_release = keymap[key][0] + 128 # code to release the key

        if (action is KeyAction.TAP):
            # @todo possibly add sleep in between the press and release
            self.sendByte(key_code_press)
            self.sendByte(key_code_release)
        elif (action is KeyAction.PRESS):
            self.sendByte(key_code_press)
        elif (action is KeyAction.RELEASE):
            self.sendByte(key_code_release)

    # clear the input buffer
    def clear(self):
        self.sendByte(56)
        for key in self.pressed_keys:
            self.releaseKey(key)

    def __del__(self):
        # make sure the buffer is clear
        self.clear

        self.com.close()

# -------- main entrypoint ---------- #

# usb = UsbToUsb()

# usb.keyAction('r', KeyAction.PRESS)


# ------------------------------ #


