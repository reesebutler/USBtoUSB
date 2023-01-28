import sys, pygame
pygame.init()

size = width, height = 320, 240
black = 0, 0, 0

screen = pygame.display.set_mode(size)
# pygame.event.set_blocked(None)
# pygame.event.set_allowed()

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

pygame.event.set_blocked(None)
pygame.event.set_allowed(allowed)

# get a listing of all keycodes, turn it into a data structure we can use for this
pygame_keycodes = {}

for attribute in dir(pygame):
    if (attribute.startswith('K_')):
        pygame_keycodes[attribute] = getattr(pygame, attribute)

print(pygame_keycodes)

while True:
    for event in pygame.event.get():
        # allow us to close the program cleanly
        if event.type == pygame.QUIT: sys.exit()

        event_name = pygame.event.event_name(event.type)
        # create an empty set()
        

        # [k for k in lst if 'ab' in k]
        

        
        
        if event.type == pygame.KEYDOWN:
            

            if event.key == pygame.K_0:
                sys.exit()
            else:
                print(event.key)


    screen.fill(black)
    pygame.display.flip()
