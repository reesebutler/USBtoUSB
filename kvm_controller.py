from usbtousb import UsbToUsb
from usbtousb import KeyAction
from time import sleep
import getpass
import sys
import argparse

parser = argparse.ArgumentParser(
    description='KVM Controller',
)

parser.add_argument('-d', '--device', help='Specify the device you want to switch to, optionally with a specific display after a comma. i.e. -d 1 would switch to device 1. -d 2,1 would switch to device 2 on display 1')
parser.add_argument('-t', '--toggle', help='Toggle input between the devices currently being displayed.', action='store_true')
parser.add_argument('-ta', '--toggle_audio', help='Toggle audio output between the devices currently being displayed.', action='store_true')
parser.add_argument('-tu', '--toggle_usb', help='Toggle USB devices between the host devices currently being displayed.', action='store_true')
parser.add_argument('-i', '--input', nargs='?', default=None, const=True, help='Translate the input as key presses on the destination keyboard.')
parser.add_argument('--input_delay', type=int, help='Wait for input_delay seconds before typing -i input.')

def doubleTapControl():
    usb.keyAction('R_CTRL', KeyAction.TAP)
    sleep(delay_between_pressing_keys)
    usb.keyAction('R_CTRL', KeyAction.TAP)
    sleep(delay_between_pressing_keys)

def switchToDeviceOnDisplay(device: int, display: str = None):
    key_name = None

    if (display is not None): display = display.lower()

    if display == 'a':
        key_name = 'L_ARROW'
    elif display == 'b':
        key_name = 'DN_ARROW'
    elif display == 'c':
        key_name = 'R_ARROW'
    elif display != None:
        print('Display ' + display + ' is invalid. Valid values are A, B, or C')
        sys.exit()

    doubleTapControl()

    if key_name != None:
        usb.keyAction(key_name, KeyAction.TAP)
        sleep(delay_between_pressing_keys)

    usb.keyAction(str(device), KeyAction.TAP)

def toggleFocus():
    usb.keyAction('R_ALT', KeyAction.TAP)
    sleep(delay_between_pressing_keys)
    usb.keyAction('R_ALT', KeyAction.TAP)

def toggleUSBDevices():
    doubleTapControl()
    usb.keyAction('UP_ARROW', KeyAction.TAP)

def toggleAudioFocus():
    doubleTapControl()
    usb.keyAction('DN_ARROW', KeyAction.TAP)

port_name = '/dev/cu.usbserial-XXXXXXX'
usb = UsbToUsb(port_name)

args = parser.parse_args()
delay_between_pressing_keys = 0.5

device = args.device
display = None
toggle = args.toggle
toggle_audio = args.toggle_audio
toggle_usb = args.toggle_usb
input = args.input
input_delay = args.input_delay

# print(sys.stdin)
# stdin = ''.join(list(sys.stdin)).strip('\n')
# print(stdin)
# sys.exit()

device = device.split(',') if device else None

if input is True:
    try:
        input = getpass.getpass(prompt='Input: ')
    except Exception as error:
        print('ERROR', error)

if device is not None:
    if len(device) > 1: display = device[1]
    device = int(device[0])

    switchToDeviceOnDisplay(device, display)
    sleep(delay_between_pressing_keys)

if input is not None:
    if input_delay:
        toggleFocus()
        print('waiting for ' + str(input_delay) + ' seconds')
        sleep(input_delay)
        
    usb.typeOutString(input=input, delay=0.02)

if toggle is True:
    toggleFocus()

if toggle_audio is True:
    toggleAudioFocus()

if toggle_usb is True:
    toggleUSBDevices()

