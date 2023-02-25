import sys, pygame
from key_mapping import keymap
from usbtousb import UsbToUsb
from usbtousb import KeyAction
from usbtousb import MouseButton
from usbtousb import MouseScrollDirection
from string import ascii_lowercase
from threading import Event
from threading import Thread

pygame.init()
pygame.display.set_caption('Auto Typer')

# icon is curtesy of Stockio.com, https://www.stockio.com/free-icon/keyboard-3
icon = pygame.image.load('assets/keyboard_icon.png')
pygame.display.set_icon(icon)

size = width, height = 320, 240
black = 0, 0, 0

screen = pygame.display.set_mode(size)

# I'm leaving these here for now as a reference
# blocked = [
#     pygame.WINDOWMOVED,
#     pygame.WINDOWLEAVE,
#     pygame.WINDOWENTER,
#     pygame.MOUSEMOTION,
#     pygame.AUDIODEVICEADDED,
#     pygame.WINDOWSHOWN,
#     pygame.VIDEOEXPOSE,
#     pygame.WINDOWEXPOSED,
#     pygame.WINDOWFOCUSLOST,
#     pygame.WINDOWFOCUSGAINED
# ]

allowed = [
    pygame.MOUSEMOTION,
    pygame.MOUSEWHEEL,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP,
    pygame.KEYDOWN,
    pygame.KEYUP,
    pygame.WINDOWCLOSE
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
pygame_keycode_map = {}
for key_name in pygame_key_names:
    pygame_keycode_map[getattr(pygame, key_name)] = key_name

# key a dictionary with pygame key names as the keys, and USBtoUSB key names as the values
pygame_to_usb_map = {}
for usb_key_name, usb_key_info in keymap.items():
    pygame_key_name = usb_key_info[1]

    if len(pygame_key_name) == 0:
        continue

    pygame_to_usb_map[pygame_key_name] = usb_key_name

# key a dictionary with key characters as the keys, and USBtoUSB key names as the values
# this lets us know how to type characters that require the shift key
shift_key_map = {
    ' ': 'SPACE', # hardcode this one because I'm lazy
}
for usb_key_name, usb_key_info in keymap.items():
    # I used ">=" here just in case I decide to start using more than 3 elements in these lists. I shouldn't. But just in case.
    if len(usb_key_info) >= 3:
        key_that_needs_shift = usb_key_info[2]
        shift_key_map[key_that_needs_shift] = usb_key_name

# also add capital letters to our shift_key_map
for letter in ascii_lowercase:
    shift_key_map[letter.capitalize()] = letter

# we need to keep track of what keys are actively being pressed, so that we can recognize keyboard shortcuts
pressed = set()
shortcuts = {
    'lock_to_window': {pygame.K_RSUPER, pygame.K_LALT, pygame.K_RETURN},
    'quit': {pygame.K_RSUPER, pygame.K_LALT, pygame.K_q},
    'paste': {pygame.K_RSUPER, pygame.K_LALT, pygame.K_v},
    'paste_with_shift': {pygame.K_RSUPER, pygame.K_LALT, pygame.K_LSHIFT, pygame.K_v}
}

def shortcutIsPressed(shortcut: str):
    shortcutIsPressed = pressed == shortcuts.get(shortcut)

    # make sure the shortcut keys are released/un-pressed
    if shortcutIsPressed is True:
        usb.clear()
        pressed.clear()

    return shortcutIsPressed

paste_thread = None
paste_thread_should_close = Event()

def pasteFromClipboard(should_hold_shift_for_newlines: bool = False):
    clipboard = pygame.scrap.get("text/plain;charset=utf-8").decode()
    clipboard = clipboard.splitlines() # make sure we're aware of any line breaks

    print('pasting...')

    # translate each clipboard character into the appropriate key press(es)
    for i, line in enumerate(clipboard):
        for char in line:
            if paste_thread_should_close.is_set():
                paste_thread_should_close.clear()
                print('canceled paste')
                return

            pressed = False

            # the key is in the mapping, and can be pressed without the shift key
            if char in keymap:

                usb.keyAction(char, KeyAction.TAP, True)
                pressed = True

            # the key is in the mapping, but needs to be pressed with the shift key
            if (char in shift_key_map):
                usb_unshifted_key = shift_key_map[char]

                usb.keyAction('L_SHIFT', KeyAction.PRESS, should_delay=True)
                usb.keyAction(usb_unshifted_key, KeyAction.TAP, should_delay=True)
                usb.keyAction('L_SHIFT', KeyAction.RELEASE, should_delay=True)
                pressed = True

            # let the user know there was a value in their clipboard that couldn't be reproduced
            if (pressed is False): print("unable to type '" + char + "' from clipboard")

        # This is not the last line of text in a multi-line clipboard value, so press the enter key
        if i + 1 < len(clipboard):
            if should_hold_shift_for_newlines: usb.keyAction('L_SHIFT', KeyAction.PRESS, should_delay=True)
            usb.keyAction('ENTER', KeyAction.TAP, should_delay=True)
            if should_hold_shift_for_newlines: usb.keyAction('L_SHIFT', KeyAction.RELEASE, should_delay=True)

locked_to_window = False
mouse_queue_has_input = False
mouse_queue_last_poll = pygame.time.get_ticks()

while True:
    for event in pygame.event.get():
        # allow us to close the program cleanly
        if event.type in (pygame.QUIT, pygame.WINDOWCLOSE): sys.exit()

        # handle key presses
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            # keep track of which keys are currently being pressed
            if (event.type == pygame.KEYDOWN):
                pressed.add(event.key)
            else: 
                pressed.discard(event.key)

            if shortcutIsPressed('quit'):
                # make sure we stop any active paste thread
                if paste_thread is not None and paste_thread.is_alive():
                    paste_thread_should_close.set()
                    paste_thread.join()
                
                print('\nlater alligator')
                sys.exit()

            if paste_thread is not None and paste_thread.is_alive():
                # the escape key was pressed, so let the paste thread know it should close
                if event.key == pygame.K_ESCAPE:
                    paste_thread_should_close.set()

                # don't process other key input while the paste thread is active
                continue;

            # handle pasting from clipboard
            should_paste = False
            should_hold_shift_for_newlines = False

            if shortcutIsPressed('paste'):
                should_paste = True

            if shortcutIsPressed('paste_with_shift'):
                should_paste = True
                should_hold_shift_for_newlines = True

            if should_paste:
                # we don't want pygame to block, so start a new thread to do the actual "pasting"
                paste_thread = Thread(target=pasteFromClipboard, args=[should_hold_shift_for_newlines])
                paste_thread.start()

                continue

            # toggle input locking
            if shortcutIsPressed('lock_to_window'):
                locked_to_window = False if pygame.event.get_grab() else True
                pygame.mouse.set_visible(not locked_to_window) # hide the mouse cursor when locked, show it when unlocked
                pygame.event.set_grab(locked_to_window)

                continue

            pygame_key_name = pygame_keycode_map[event.key]
            usb_key_name = pygame_to_usb_map[pygame_key_name]

            if event.type == pygame.KEYDOWN:
                usb_key_action = KeyAction.PRESS
            else:
                usb_key_action = KeyAction.RELEASE

            # press or release the destination key
            usb.keyAction(usb_key_name, usb_key_action)

        # handle mouse movement
        if locked_to_window and event.type == pygame.MOUSEMOTION:
            usb.moveMouseInDirection(event.rel[0], event.rel[1], apply_immediately=False)
            mouse_queue_has_input = True

        # handle mouse clicks
        if locked_to_window and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if event.type == pygame.MOUSEBUTTONDOWN:
                mode = KeyAction.PRESS
            else:
                mode = KeyAction.RELEASE

            button = None

            if event.button == 1:
                button = MouseButton.LEFT
            elif event.button == 2:
                button = MouseButton.MIDDLE
            elif event.button == 3:
                button = MouseButton.RIGHT

            if button != None:
                usb.mouseButtonAction(button, mode, apply_immediately=False)
                mouse_queue_has_input = True

        # handle mouse scrolling
        # TODO implement scroll smoothing/momentum
        if locked_to_window and event.type == pygame.MOUSEWHEEL:
            # the USBtoUSB device can only support vertical scrolling, unfortunately, so we'll ignore any horizontal scrolling pygame tells us about
            scroll_value = event.y

            if scroll_value != 0:
                mouse_queue_has_input = True
                direction = None

                if scroll_value < 0:
                    direction = MouseScrollDirection.UP
                else:
                    direction = MouseScrollDirection.DOWN

                usb.mouseScrollAction(direction, scroll_value, apply_immediately=False)

        # TODO mouse auto-jiggler
        # if not locked_to_window:

        # send a single updated mouse control packet for movement, clicks, and scrolling
        if mouse_queue_has_input:
            mouse_queue_has_input = False
            usb.sendMouseControlPacket()


        # TODO make it so you can pipe text input into the script, to directly make it type out the given text

    screen.fill(black)

    pygame.display.flip()
