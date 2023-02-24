import os
import random
import serial
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
        # load in our .env variables
        load_dotenv()
        port_name = os.environ.get('PORT_NAME');
        self.delay_lower_bound = os.environ.get('DELAY_LOWER_BOUND');
        self.delay_upper_bound = os.environ.get('DELAY_UPPER_BOUND');

        # connect to the USBtoUSB com port
        self.com = serial.Serial(port_name, self.baudrate, self.bytesize, self.parity, self.stopbits)

    def sendByte(self, value: int):
        self.com.write((value).to_bytes(1, 'big', signed = False))

    def keyAction(self, key: str, action: KeyAction, should_delay: bool = False):
        key_code_press = keymap[key][0] # code to press down the key
        key_code_release = keymap[key][0] + 128 # code to release the key
        delay = 0.005 # we need some amount of delay at minimum when lots of keys are going to be pressed in sequence

        # let's see if we have the environment variables we need to insert a delay after/between keypresses
        if should_delay:
            if self.delay_lower_bound is not None: 
                delay = float(self.delay_lower_bound)

            # an upper bound was specified, so let's find a random amount of time to wait
            if self.delay_upper_bound is not None: 
                delay = random.uniform(delay, float(self.delay_upper_bound))

        if (action is KeyAction.TAP):
            self.sendByte(key_code_press)

            # we need to delay at least a little bit between pressing and releasing the key, otherwise the key may not be released properly
            sleep(0.005)

            self.sendByte(key_code_release) 
        elif (action is KeyAction.PRESS):
            self.sendByte(key_code_press)
        elif (action is KeyAction.RELEASE):
            self.sendByte(key_code_release)

        if should_delay: sleep(delay)

    # clear the input buffer
    def clear(self):
        self.sendByte(56)

    def __del__(self):
        # make sure the device buffer is clear
        self.clear

        # cleanly kill our connection to the device
        self.com.close()

# -------- main entrypoint ---------- #

# usb = UsbToUsb()

# usb.keyAction('r', KeyAction.PRESS)


# ------------------------------ #


