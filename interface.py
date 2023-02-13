import sys, pygame
from key_mapping import keymap
from usbtousb import UsbToUsb
from usbtousb import KeyAction
from pprint import pprint
pygame.init()

size = width, height = 320, 240
black = 0, 0, 0

screen = pygame.display.set_mode(size)

blocked = [
    pygame.WINDOWMOVED,
    pygame.WINDOWLEAVE,
    pygame.WINDOWENTER,
    # pygame.MOUSEMOTION,
    pygame.AUDIODEVICEADDED,
    pygame.WINDOWSHOWN,
    pygame.VIDEOEXPOSE,
    pygame.WINDOWEXPOSED,
    pygame.WINDOWFOCUSLOST,
    pygame.WINDOWFOCUSGAINED
]

allowed = [
    # pygame.ACTIVEEVENT,
    pygame.MOUSEWHEEL,
    pygame.KEYDOWN,
    pygame.KEYUP,
    pygame.TEXTINPUT,
    pygame.MOUSEMOTION,
]

pygame.event.set_blocked(None) # block all events
pygame.event.set_allowed(allowed) # now allow only specific events

# initialize the USBtoUSB controller
usb = UsbToUsb()

# clipboard (pasting) support
pygame.scrap.init()
pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)

# get all the pygame property names that begin with 'K_'
pygame_key_names = filter(lambda property: property.startswith('K_'), dir(pygame))

# turn them into a dictionary where keys are the key codes, and the values are the pygame key property names
pygame_keymap = {}
for key_name in pygame_key_names:
    pygame_keymap[getattr(pygame, key_name)] = key_name

# key a dictionary with pygame key names as the keys, and USBtoUSB key names as the values
usb_keymap = {}
for usb_key_name, usb_key_info in keymap.items():
    pygame_key_name = usb_key_info[1]

    if len(pygame_key_name) == 0:
        continue

    usb_keymap[pygame_key_name] = usb_key_name

# we need to keep track of what keys are actively being pressed, so that we can recognize keyboard shortcuts
pressed = set()
shortcuts = {
    'lock_to_window': {pygame.K_RSUPER, pygame.K_LALT, pygame.K_RETURN},
    'quit': {pygame.K_RSUPER, pygame.K_LALT, pygame.K_q},
    'paste': {pygame.K_RSUPER, pygame.K_LALT, pygame.K_v}
}

def shortcutIsPressed(shortcut: str): return pressed == shortcuts.get(shortcut)

while True:
    for event in pygame.event.get():
        # allow us to close the program cleanly
        if event.type == pygame.QUIT: sys.exit()

        # handle key presses
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            # keep track of which keys are currently being pressed
            if (event.type == pygame.KEYDOWN):
                pressed.add(event.key)
            else: 
                pressed.remove(event.key)

            if shortcutIsPressed('quit'):
                sys.exit()

            if shortcutIsPressed('paste'):
                clipboard = pygame.scrap.get("text/plain;charset=utf-8").decode()


            pygame_key_name = pygame_keymap[event.key]
            usb_key_name = usb_keymap[pygame_key_name]

            if event.type == pygame.KEYDOWN:
                usb_key_action = KeyAction.PRESS
            else:
                usb_key_action = KeyAction.RELEASE

            # press or release the destination key
            usb.keyAction(usb_key_name, usb_key_action)

        # TODO mouse control

    screen.fill(black)

    pygame.display.flip()
