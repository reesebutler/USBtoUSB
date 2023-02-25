import os
import random
import serial
from dotenv import load_dotenv
from time import sleep
from enum import auto
from enum import Enum
from key_mapping import keymap
from numpy import clip

class KeyAction(Enum):
    TAP = auto()
    RELEASE = auto()
    PRESS = auto()

class MouseButton(Enum):
    LEFT = auto()
    MIDDLE = auto()
    RIGHT = auto()

class MouseScrollDirection(Enum):
    UP = auto()
    DOWN = auto()

class UsbToUsb:
    # the settings used to connect here, are those required by the USBtoUSB (Hagstrom Electronics product) hardware
    baudrate = 19200
    bytesize = 8
    parity = serial.PARITY_NONE
    stopbits = serial.STOPBITS_ONE

    def __init__(self):
        # load in our .env variables
        load_dotenv()
        port_name = os.environ.get('PORT_NAME')
        self.delay_lower_bound = os.environ.get('DELAY_LOWER_BOUND')
        self.delay_upper_bound = os.environ.get('DELAY_UPPER_BOUND')

        # initialize our mouse data
        self.mouse_x_position = 0
        self.mouse_x_position_max = int(os.environ.get('TARGET_SCREEN_X_SIZE')) - 1
        self.mouse_y_position = 0
        self.mouse_y_position_max = int(os.environ.get('TARGET_SCREEN_Y_SIZE')) - 1
        self.left_mouse_pressed = False
        self.right_mouse_pressed = False
        self.middle_mouse_pressed = False
        self.scroll_direction = 0
        self.scroll_amplitude = 0
        self.invert_scroll_direction = os.environ.get('INVERT_SCROLL_DIRECTION') == 'True'

        # connect to the USBtoUSB com port
        self.com = serial.Serial(port_name, self.baudrate, self.bytesize, self.parity, self.stopbits)

    def sendBytes(self, value: int, length: int = 1, debug: bool = False):
        for i in range(0, length):
            # get just one byte at a time, going from most to least significant
            which_byte = length - i - 1
            byte_as_int = value >> (which_byte * 8) & 255
            byte = (byte_as_int).to_bytes(1, 'big', signed = False)

            if debug: print(byte)
            self.com.write(byte)

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
            self.sendBytes(key_code_press)

            # we need to delay at least a little bit between pressing and releasing the key, otherwise the key may not be released properly
            sleep(0.005)

            self.sendBytes(key_code_release) 
        elif (action is KeyAction.PRESS):
            self.sendBytes(key_code_press)
        elif (action is KeyAction.RELEASE):
            self.sendBytes(key_code_release)

        if should_delay: sleep(delay)

    def moveMouseToPosition(self, x_position: int, y_position: int, apply_immediately: bool = True):
        self.mouse_x_position = x_position
        self.mouse_y_position = y_position

        if apply_immediately: self.sendMouseControlPacket()
    
    def moveMouseInDirection(self, x_change: int, y_change: int, apply_immediately: bool = True):
        new_x_position = self.mouse_x_position + x_change
        new_y_position = self.mouse_y_position + y_change

        # make sure our target mouse position stays within the correct range
        new_x_position = clip([new_x_position], 0, self.mouse_x_position_max)[0]
        new_y_position = clip([new_y_position], 0, self.mouse_y_position_max)[0]
        self.mouse_x_position = int(new_x_position)
        self.mouse_y_position = int(new_y_position)

        if apply_immediately: self.sendMouseControlPacket()

    # TODO decide on a better/consistent naming scheme for KeyAction and its associated variables
    def mouseButtonAction(self, button: MouseButton, mode: KeyAction, apply_immediately: bool = True):
        new_button_value = True if mode is KeyAction.PRESS else False

        if button is MouseButton.LEFT:
            self.left_mouse_pressed = new_button_value
        elif button is MouseButton.MIDDLE:
            self.middle_mouse_pressed = new_button_value
        elif button is MouseButton.RIGHT:
            self.right_mouse_pressed = new_button_value

        if apply_immediately: self.sendMouseControlPacket()

    def mouseScrollAction(self, direction: MouseScrollDirection, amplitude: int, apply_immediately: bool = True):
        scroll_direction = 0

        # 0 means up, and 1 means down
        if direction == MouseScrollDirection.DOWN and not self.invert_scroll_direction:
            scroll_direction = 1
        elif direction == MouseScrollDirection.UP and self.invert_scroll_direction:
            scroll_direction = 1
        
        # restrict the amplitude to fit within the (consistently) useable range of the USBtoUSB device
        new_amplitude = clip([abs(amplitude)], 0, 7)[0]
        new_amplitude = int(new_amplitude)

        # valid amplitude range for scrolling up, in bytes low to high:       001 thru 111 (1 - 7)
        # valid amplitude range for scrolling down, in bytes "low" to "high": 111 thru 000 (7 - 0)
        # We need to handle downward scrolling, because it does a few things differently
        if scroll_direction == 1:
            # the USBtoUSB device lets you have a higher amplitude when scrolling down, since 0 counts as the max scroll speed, 8.
            # I want it to feel balanced, so lower it by 1 to be in line with the allowed amplitude when scrolling up.
            new_amplitude -= 1

            # the USBtoUSB device expects the amplitude to be inverted when scrolling down, so invert it
            new_amplitude = 7 - new_amplitude

        self.scroll_direction = scroll_direction
        self.scroll_amplitude = new_amplitude

        if apply_immediately: self.sendMouseControlPacket()
    
    def sendMouseControlPacket(self):
        self.sendBytes(0) # byte 1 begins the 6 byte mouse control sequence
        self.sendBytes(self.mouse_x_position, length=2) # byte 2 + byte 3
        self.sendBytes(self.mouse_y_position, length=2) # byte 4 + byte 5

        # build byte #6: mouse wheel movement
        control_byte = 0

        control_byte |= self.scroll_direction << 7 # bit 7
        control_byte |= self.scroll_amplitude << 4 # bits 6, 5, and 4
        control_byte |= 1 << 3 # bit 3 is always 1, otherwise the entire mouse control packet will be ignored
        control_byte |= int(self.middle_mouse_pressed) << 2 # bit 2
        control_byte |= int(self.right_mouse_pressed) << 1 # bit 1
        control_byte |= int(self.left_mouse_pressed) # bit 0

        # send our newly constructed mouse control packet, which concludes the 6 byte mouse control sequence
        self.sendBytes(control_byte)

        # always reset the scroll data. Without this, we'd be scrolling forever, or even scrolling when the only action was a mouse movement
        self.scroll_direction = 0
        self.scroll_amplitude = 0

    # clear the input buffer
    def clear(self):
        self.sendBytes(56)

    def __del__(self):
        # make sure the device buffer is clear
        self.clear

        # cleanly kill our connection to the device
        self.com.close()

# -------- main entrypoint ---------- #

# usb = UsbToUsb()

# usb.keyAction('r', KeyAction.PRESS)


# ------------------------------ #


