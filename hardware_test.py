#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# hardware_test - a simple PyGame hardware tester
# Copyright (C) 2012  Chris Clark
"""Hardware test app for PyGame.

Targetted at GCW0 buttons and analog nub.
Could be made more generic via config files.
"""

import os
import sys
import time
import glob
import subprocess
from math import sin, cos, pi

import pygame
import pygame.locals

DEBUG = False
no_secs = False


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

PRESSED_DONE = BLUE
PRESSED_ACTIVE = GREEN
BOX_OUTLINE = WHITE


class TextRectException(Exception):
    # TextRect from http://www.pygame.org/pcr/text_rect/index.php
    def __init__(self, message=None):
        self.message = message
    
    def __str__(self):
        return self.message


def render_textrect(string, font, rect, text_color, background_color=None, justification=0, surface=None):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 (default) left-justified
                    1 horizontally centered
                    2 right-justified

    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    import pygame
    
    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.

    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException("The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.    
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line 
                else: 
                    final_lines.append(accumulated_line) 
                    accumulated_line = word + " " 
            final_lines.append(accumulated_line)
        else: 
            final_lines.append(requested_line) 

    # Let's try to write the text out on the surface.

    surface = surface or pygame.Surface(rect.size) 
    if background_color:
        surface.fill(background_color) 

    accumulated_height = 0 
    for line in final_lines: 
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise TextRectException("Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width - tempsurface.get_width(), accumulated_height))
            else:
                raise TextRectException("Invalid justification argument: " + str(justification))
        accumulated_height += font.size(line)[1]

    return surface


def get_time_surface(background, font_time):
    if no_secs:
        time_str = time.strftime('%H:%M')
    else:
        time_str = time.strftime('%H:%M:%S')
    time_surface = font_time.render(time_str, True, WHITE,)
    textRect = time_surface.get_rect()
    textRect.centerx = background.get_rect().centerx
    textRect.centery = background.get_rect().centery
    return time_surface, textRect

def get_countdown_surface(background, font_time, timer_count):
    time_str = 'Done in %d' % timer_count
    time_surface = font_time.render(time_str, True, WHITE,)
    textRect = time_surface.get_rect()
    #textRect.left = background.get_rect().left
    #textRect.top = background.get_rect().top
    textRect.left, textRect.top = 0, 0
    return time_surface, textRect

# OpenDingux SDL button mappings
BTN_DPAD_UP = pygame.locals.K_UP
BTN_DPAD_DOWN = pygame.locals.K_DOWN
BTN_DPAD_LEFT = pygame.locals.K_LEFT
BTN_DPAD_RIGHT = pygame.locals.K_RIGHT
BTN_A = pygame.locals.K_LCTRL
BTN_B = pygame.locals.K_LALT
BTN_X = pygame.locals.K_SPACE
BTN_Y = pygame.locals.K_LSHIFT
BTN_START = pygame.locals.K_RETURN
BTN_SELECT = pygame.locals.K_ESCAPE
BTN_LEFT_SHOULDER = pygame.locals.K_TAB
BTN_RIGHT_SHOULDER = pygame.locals.K_BACKSPACE
BTN_HOLD = pygame.locals.K_END  # NOTE OpenDingux=hold_slide
BTN_VOL_DOWN = pygame.locals.K_1
BTN_VOL_UP = pygame.locals.K_2

papk3 = {
                    'name': 'PAP KIII',
                    'background': 'pap.png',
                    'test_buttons': {
                                        BTN_DPAD_UP: (40, 40, 20, 20),
                                        BTN_DPAD_DOWN: (40, 100, 20, 20),
                                        BTN_DPAD_LEFT: (10, 70, 20, 20),
                                        BTN_DPAD_RIGHT: (70, 70, 20, 20),
                                        BTN_A: (450, 70, 20, 20),
                                        BTN_B: (420, 100, 20, 20),
                                        BTN_X: (420, 40, 20, 20),
                                        BTN_Y: (390, 70, 20, 20),
                                        BTN_START: (435, 200, 20, 20),
                                        BTN_SELECT: (405, 200, 20, 20),
                                        BTN_LEFT_SHOULDER: (30, 10, 40, 20),
                                        BTN_RIGHT_SHOULDER: (410, 10, 40, 20),
                                        BTN_HOLD: (220, 10, 40, 20),
                                        BTN_VOL_DOWN: (405, 170, 20, 20),
                                        BTN_VOL_UP: (435, 170, 20, 20)
                                    },
                }

a320 = {
                    'name': 'Dingoo A320',
                    'background': 'a320.png',
                    'test_buttons': {
                                        BTN_DPAD_UP: (40, 40, 20, 20),
                                        BTN_DPAD_DOWN: (40, 100, 20, 20),
                                        BTN_DPAD_LEFT: (10, 70, 20, 20),
                                        BTN_DPAD_RIGHT: (70, 70, 20, 20),
                                        BTN_A: (280, 70, 20, 20),
                                        BTN_B: (250, 100, 20, 20),
                                        BTN_X: (250, 40, 20, 20),
                                        BTN_Y: (220, 70, 20, 20),
                                        BTN_START: (220, 170, 20, 20),
                                        BTN_SELECT: (70, 170, 20, 20),
                                        BTN_LEFT_SHOULDER: (30, 10, 40, 20),
                                        BTN_RIGHT_SHOULDER: (240, 10, 40, 20),
                                        BTN_HOLD: (280, 130, 20, 20),
                                        0: (280, 100, 20, 20),  # Power
                                    },
                }

sound_buttons = {
                    BTN_START: 'audiocheck.net_c.wav',
                    BTN_LEFT_SHOULDER: 'audiocheck.net_l.wav',
                    BTN_RIGHT_SHOULDER: 'audiocheck.net_r.wav',
                }

ESCAPE_IS_QUIT = True
ESCAPE_IS_QUIT = False
TEST_TIMEOUT = 10 * 1000  # 10 seconds


def test_sound(clock, screen, font_time, font_text, j):
    image_filename = 'wallpaper.png'
    my_rect = screen.get_rect()
    
    try:
        # NOTE image needs to match screen res
        # TODO handle images too small/large
        background = pygame.image.load(image_filename)
        background = background.convert()
    except pygame.error:
        background = pygame.Surface(my_rect.size)
    
    text_str = '''
    START=both
    Left shoulder=left
    Right shoulder=right
    SELECT=quit'''
    rendered_text = render_textrect(text_str, font_text, my_rect, WHITE, surface=background)
    if rendered_text:
        background.blit(rendered_text, my_rect.topleft)

    keepGoing = True
    while keepGoing:
        #clock.tick(4)  # 4 times a second
        clock.tick(60)  # 60 times a second
        bg = background.copy()
        # update an on screen clock to show activity (and not hung)
        # TODO replace with a count down timer and have button test auto quit?
        time_surface, textRect = get_time_surface(bg, font_time)
        bg.blit(time_surface, textRect)
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                keepGoing = False  # Quit
            elif event.type == pygame.KEYDOWN:
                try:
                    sound = sound_buttons[event.key]
                    sound.play()
                except KeyError:
                    # TODO display to screen too?
                    print 'Unsupported button/key pressed', event.key
                if event.key == BTN_SELECT:
                    keepGoing = False  # Quit
            
        screen.blit(bg, (0, 0))
        pygame.display.flip()


class BaseException(Exception):
    '''Base exception'''


class SpawnError(BaseException):
    '''Spawned process exception'''


def execute(command):
    errors_output = subprocess.PIPE
    
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    data = p.stdout.read()
    data_err = p.stderr.read()
    
    rc = p.wait()
    
    if rc:
        raise SpawnError('error spawning rc=%r %r stderr=%r stdout=%r' % (rc, command, data_err, data))
    
    return data, data_err


def test_mic(clock, screen, font_time, font_text, j):
    temp_filename = '/tmp/delme.wav'
    num_secs = 3
    command = ['arecord', '--nonblock', '--format=S16_LE', '-d %d' % num_secs, '--rate=11025', '--channels=1', temp_filename]
    
    class FakeSound(object):
        def play(self):
            pass
    
    sound = FakeSound()

    image_filename = 'wallpaper.png'
    my_rect = screen.get_rect()
    
    try:
        # NOTE image needs to match screen res
        # TODO handle images too small/large
        background = pygame.image.load(image_filename)
        background = background.convert()
    except pygame.error:
        background = pygame.Surface(my_rect.size)
    
    text_str = '''Microphone Test
    Left shoulder=record %d secs
    Right shoulder=play
    SELECT=quit''' % num_secs
    rendered_text = render_textrect(text_str, font_text, my_rect, WHITE, surface=background)
    if rendered_text:
        background.blit(rendered_text, my_rect.topleft)

    keepGoing = True
    while keepGoing:
        #clock.tick(4)  # 4 times a second
        clock.tick(60)  # 60 times a second
        bg = background.copy()
        # update an on screen clock to show activity (and not hung)
        # TODO replace with a count down timer and have button test auto quit?
        time_surface, textRect = get_time_surface(bg, font_time)
        bg.blit(time_surface, textRect)
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                keepGoing = False  # Quit
            elif event.type == pygame.KEYDOWN:
                if event.key == BTN_SELECT:
                    keepGoing = False  # Quit
                elif event.key == BTN_LEFT_SHOULDER:
                    d = execute(command)
                    # TODO sound a ping noise to show recording completed
                    print 'DEBUG', d
                    sound = pygame.mixer.Sound(temp_filename)
                    #sound = pygame.mixer.Sound('audiocheck.net_c.wav')  # DEBUG
                elif event.key == BTN_RIGHT_SHOULDER:
                    sound.play()
                else:
                    # TODO display to screen too?
                    print 'Unsupported button/key pressed', event.key
            
        screen.blit(bg, (0, 0))
        pygame.display.flip()

    # FIXME TODO delete temp_filename


analog_deadzone = 0.01  # basically error margin to ignore
def test_buttons(clock, screen, font_time, font_text, j):
    test_hardware = dumb_system_id()
    image_filename = test_hardware['background']
    test_buttons = test_hardware['test_buttons']
    
    my_rect = screen.get_rect()
    no_buttons_pressed = pygame.time.get_ticks()
    
    try:
        # NOTE image needs to match screen res
        # TODO handle images too small/large
        background = pygame.image.load(image_filename)
        background = background.convert()
    except pygame.error:
        background = pygame.Surface(my_rect.size)
        # draw one pixel line around edge
        pygame.draw.rect(background, BOX_OUTLINE, my_rect, 1)

    bg = background.copy()
    # TODO? Display system name test_hardware['name']
    time_surface, textRect = get_time_surface(bg, font_time)
    bg.blit(time_surface, textRect)
    
    for x in test_buttons:
        box_details = test_buttons[x]
        pygame.draw.rect(background, BOX_OUTLINE, box_details)
    keepGoing = True
    really_quit = False
    while keepGoing:
        #clock.tick(4)  # 4 times a second
        clock.tick(60)  # 60 times a second
        bg = background.copy()
        # update an on screen clock to show activity (and not hung)
        # TODO replace with a count down timer and have button test auto quit?
        time_surface, textRect = get_time_surface(bg, font_time)
        bg.blit(time_surface, textRect)
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                keepGoing = False  # Quit
                really_quit = True
            elif event.type == pygame.KEYDOWN:
                no_buttons_pressed = pygame.time.get_ticks()
                #print pygame.key.get_pressed()
                try:
                    box_details = test_buttons[event.key]
                    if event.key != 0:
                        pygame.draw.ellipse(background, PRESSED_ACTIVE, box_details)
                    else:
                        # OpenDingux hack
                        pygame.draw.rect(background, RED, box_details)
                except KeyError:
                    # TODO display to screen too?
                    print 'WARNING Unsupported button/key pressed', event.key
                if ESCAPE_IS_QUIT and event.key == pygame.locals.K_ESCAPE:
                    # FIXME better quit option, I'm tempted to NOT have one and let OS do it but screen clean up under OpenDingux is not great when abnormally terminating processes
                    keepGoing = False  # Quit
            elif event.type == pygame.KEYUP:
                try:
                    box_details = test_buttons[event.key]
                    pygame.draw.rect(background, PRESSED_DONE, box_details)
                except KeyError:
                    print 'WARNING Unsupported button/key released', event.key
            else:
                print 'WARNING unknown event occurred'
            
        # Joystick
        if j:
            # FIXME this is dirty... TODO use render_textrect() and check ALL Joystick axis/buttons
            jstick_str = ''
            i = 0
            axisread = j.get_axis(i)
            if abs(axisread) > analog_deadzone:
                no_buttons_pressed = pygame.time.get_ticks()
                jstick_str = 'Axis %i reads %.2f' % (i, axisread)
            text = font_text.render(jstick_str, True, WHITE)
            textRect = text.get_rect()
            textRect.centerx = bg.get_rect().centerx
            textRect.centery = bg.get_rect().bottom - textRect.height
            if jstick_str:
                bg.blit(text, textRect)
            temp_y = textRect.centery

            jstick_str = ''
            i = 1
            axisread = j.get_axis(i)
            if abs(axisread) > analog_deadzone:
                no_buttons_pressed = pygame.time.get_ticks()
                jstick_str = 'Axis %i reads %.2f' % (i, axisread)
            text = font_text.render(jstick_str, True, WHITE)
            textRect = text.get_rect()
            textRect.centerx = bg.get_rect().centerx
            textRect.centery = temp_y - textRect.height
            if jstick_str:
                bg.blit(text, textRect)
        else:
            # no joystick
            jstick_str = 'no joystick found'
            text = font_text.render(jstick_str, True, WHITE)
            textRect = text.get_rect()
            textRect.centerx = bg.get_rect().centerx
            textRect.centery = bg.get_rect().bottom - textRect.height
            if jstick_str:
                bg.blit(text, textRect)

        screen.blit(bg, (0, 0))
        pygame.display.flip()
        if not ESCAPE_IS_QUIT:
            if (pygame.time.get_ticks() - no_buttons_pressed) >= TEST_TIMEOUT:
                keepGoing = False  # Quit


def test_analog1(clock, screen, font_time, font_text, j):
    test_hardware = dumb_system_id()
    image_filename = test_hardware['background']
    
    my_rect = screen.get_rect()
    no_buttons_pressed = pygame.time.get_ticks()
    
    try:
        # NOTE image needs to match screen res
        # TODO handle images too small/large
        background = pygame.image.load(image_filename)
        background = background.convert()
    except pygame.error:
        background = pygame.Surface(my_rect.size)

    bg = background.copy()
    screen_centerx = bg.get_rect().centerx
    screen_centery = bg.get_rect().centery
    # draw one pixel line around edge of analog display range box
    #box_factor = 1
    box_factor = 2  # 1/2 (0.5)
    #box_factor = 3  # 1/3 (0.33)
    box_factor = 100 / box_factor
    pygame.draw.rect(background, BOX_OUTLINE, ((screen_centerx - 1) - box_factor, (screen_centery - 1) - box_factor, (box_factor * 2) + 3, (box_factor * 2) + 3), 1)
    num_axes = 0
    if j:
        num_axes = j.get_numaxes()
        #num_axes = 2  # DEBUG pretend to be gcw0

    # TODO? Display system name test_hardware['name']
    time_to_quit = TEST_TIMEOUT - (pygame.time.get_ticks() - no_buttons_pressed)
    time_surface, textRect = get_countdown_surface(bg, font_time, time_to_quit)
    bg.blit(time_surface, textRect)
    
    keepGoing = True
    really_quit = False
    #pygame.key.set_repeat(int(1000 * 0.1), int(1000 * 0.1))
    #pygame.key.set_repeat(1, 50)
    #pygame.key.set_repeat(40, 30)
    pygame.key.set_repeat(500, 30)
    global analog_deadzone
    while keepGoing:
        #clock.tick(4)  # 4 times a second
        clock.tick(60)  # 60 times a second
        bg = background.copy()
        # update an on screen clock to show activity (and not hung)
        # TODO replace with a count down timer and have button test auto quit?
        time_to_quit = TEST_TIMEOUT - (pygame.time.get_ticks() - no_buttons_pressed)
        time_surface, textRect = get_countdown_surface(bg, font_time, time_to_quit)
        bg.blit(time_surface, textRect)
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                keepGoing = False  # Quit
                really_quit = True
            elif event.type == pygame.KEYDOWN:
                no_buttons_pressed = pygame.time.get_ticks()
                if event.key in [pygame.locals.K_UP, BTN_A,  pygame.locals.K_a]:
                    analog_deadzone += 0.01
                    analog_deadzone = min(analog_deadzone, 1.0)
                elif event.key in [pygame.locals.K_DOWN, BTN_B, ]:
                    analog_deadzone -= 0.01
                    analog_deadzone = max(analog_deadzone, 0.0)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.locals.K_ESCAPE:
                    keepGoing = False  # Quit
                elif event.key in [pygame.locals.K_RIGHT, BTN_X, ]:
                    analog_deadzone += 0.01
                    analog_deadzone = min(analog_deadzone, 1.0)
                elif event.key in [pygame.locals.K_LEFT, BTN_Y, ]:
                    analog_deadzone -= 0.01
                    analog_deadzone = max(analog_deadzone, 0.0)
        
        # Joystick
        if j:
            if num_axes == 2:
                axis_x, axis_y = 0, 0
                jstick_str = ''
                i = 0
                axisread = j.get_axis(i)
                if abs(axisread) > analog_deadzone:
                    axis_x = int(axisread * box_factor)
                    no_buttons_pressed = pygame.time.get_ticks()
                    jstick_str = 'Axis %i reads %.2f' % (i, axisread)
                text = font_text.render(jstick_str, True, WHITE)
                textRect = text.get_rect()
                textRect.centerx = bg.get_rect().centerx
                textRect.centery = bg.get_rect().bottom - textRect.height
                if jstick_str:
                    bg.blit(text, textRect)
                temp_y = textRect.centery

                jstick_str = ''
                i = 1
                axisread = j.get_axis(i)
                if abs(axisread) > analog_deadzone:
                    axis_y = int(axisread * box_factor)
                    no_buttons_pressed = pygame.time.get_ticks()
                    jstick_str = 'Axis %i reads %.2f' % (i, axisread)
                text = font_text.render(jstick_str, True, WHITE)
                textRect = text.get_rect()
                textRect.centerx = bg.get_rect().centerx
                textRect.centery = temp_y - textRect.height
                if jstick_str:
                    bg.blit(text, textRect)
                pygame.draw.rect(bg, RED, ((screen_centerx - 1) + axis_x, (screen_centery - 1) + axis_y, 3, 3))
                text = font_text.render('Deadzone %.2f' % analog_deadzone, True, WHITE)
                textRect = text.get_rect()
                textRect.left = 5
                textRect.top = 30
                bg.blit(text, textRect)
            else:
                jstick_str = ''
                for i in range(0, j.get_numaxes()):
                    axisread = j.get_axis(i)
                    if abs(axisread) > analog_deadzone:
                        no_buttons_pressed = pygame.time.get_ticks()
                        jstick_str = jstick_str +'\n' + 'Axis %i reads %.2f' % (i, axisread)
                for i in range(0, j.get_numbuttons()):
                    buttonread = j.get_button(i)
                    if buttonread != 0:
                        no_buttons_pressed = pygame.time.get_ticks()
                        jstick_str = jstick_str +'\n' + 'Button %i reads %i' % (i, buttonread)
                if jstick_str:
                    rendered_text = render_textrect(jstick_str, font_text, my_rect, WHITE, surface=None)
                    if rendered_text:
                        bg.blit(rendered_text, my_rect.topleft)
        else:
            # no joystick
            jstick_str = 'no joystick found'
            text = font_text.render(jstick_str, True, WHITE)
            textRect = text.get_rect()
            textRect.centerx = bg.get_rect().centerx
            textRect.centery = bg.get_rect().bottom - textRect.height
            if jstick_str:
                bg.blit(text, textRect)

        bg.set_at((screen_centerx, screen_centery), WHITE)  # draw single pixel dot at center

        screen.blit(bg, (0, 0))
        pygame.display.flip()
        if not ESCAPE_IS_QUIT:
            if time_to_quit <= 0:
                keepGoing = False  # Quit
    pygame.key.set_repeat()

def test_analog2(clock, screen, font_time, font_text, j):
    """Tests second joystick (i.e. #1, #0 is the first one).
    On GCW0 device this is the gsensor if the gsensor userspace driver
    has been successfully installed and ran.
    """
    test_hardware = dumb_system_id()
    image_filename = test_hardware['background']
    
    try:
        j = pygame.joystick.Joystick(1)
        j.init()
        print 'Initialized Joystick : %s' % j.get_name()
    except pygame.error:
        j = None
    # open number 2 joystick (on GCW) gsensor driver stick)
    
    my_rect = screen.get_rect()
    no_buttons_pressed = pygame.time.get_ticks()
    
    try:
        # NOTE image needs to match screen res
        # TODO handle images too small/large
        background = pygame.image.load(image_filename)
        background = background.convert()
    except pygame.error:
        background = pygame.Surface(my_rect.size)

    bg = background.copy()
    screen_centerx = bg.get_rect().centerx
    screen_centery = bg.get_rect().centery
    # draw one pixel line around edge of analog display range box
    #box_factor = 1
    box_factor = 2  # 1/2 (0.5)
    #box_factor = 3  # 1/3 (0.33)
    box_factor = 100 / box_factor
    pygame.draw.rect(background, BOX_OUTLINE, ((screen_centerx - 1) - box_factor, (screen_centery - 1) - box_factor, (box_factor * 2) + 3, (box_factor * 2) + 3), 1)
    num_axes = 0
    if j:
        num_axes = j.get_numaxes()
        #num_axes = 2  # DEBUG pretend to be gcw0

    # TODO? Display system name test_hardware['name']
    time_to_quit = TEST_TIMEOUT - (pygame.time.get_ticks() - no_buttons_pressed)
    time_surface, textRect = get_countdown_surface(bg, font_time, time_to_quit)
    bg.blit(time_surface, textRect)
    
    keepGoing = True
    really_quit = False
    #pygame.key.set_repeat(int(1000 * 0.1), int(1000 * 0.1))
    #pygame.key.set_repeat(1, 50)
    #pygame.key.set_repeat(40, 30)
    pygame.key.set_repeat(500, 30)
    global analog_deadzone
    while keepGoing:
        #clock.tick(4)  # 4 times a second
        clock.tick(60)  # 60 times a second
        bg = background.copy()
        # update an on screen clock to show activity (and not hung)
        # TODO replace with a count down timer and have button test auto quit?
        time_to_quit = TEST_TIMEOUT - (pygame.time.get_ticks() - no_buttons_pressed)
        time_surface, textRect = get_countdown_surface(bg, font_time, time_to_quit)
        bg.blit(time_surface, textRect)
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                keepGoing = False  # Quit
                really_quit = True
            elif event.type == pygame.KEYDOWN:
                no_buttons_pressed = pygame.time.get_ticks()
                if event.key in [pygame.locals.K_UP, BTN_A,  pygame.locals.K_a]:
                    analog_deadzone += 0.01
                    analog_deadzone = min(analog_deadzone, 1.0)
                elif event.key in [pygame.locals.K_DOWN, BTN_B, ]:
                    analog_deadzone -= 0.01
                    analog_deadzone = max(analog_deadzone, 0.0)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.locals.K_ESCAPE:
                    keepGoing = False  # Quit
                elif event.key in [pygame.locals.K_RIGHT, BTN_X, ]:
                    analog_deadzone += 0.01
                    analog_deadzone = min(analog_deadzone, 1.0)
                elif event.key in [pygame.locals.K_LEFT, BTN_Y, ]:
                    analog_deadzone -= 0.01
                    analog_deadzone = max(analog_deadzone, 0.0)
        
        # Joystick
        if j:
            if num_axes == 2:
                axis_x, axis_y = 0, 0
                jstick_str = ''
                i = 0
                axisread = j.get_axis(i)
                if abs(axisread) > analog_deadzone:
                    axis_x = int(axisread * box_factor)
                    no_buttons_pressed = pygame.time.get_ticks()
                    jstick_str = 'Axis %i reads %.2f' % (i, axisread)
                text = font_text.render(jstick_str, True, WHITE)
                textRect = text.get_rect()
                textRect.centerx = bg.get_rect().centerx
                textRect.centery = bg.get_rect().bottom - textRect.height
                if jstick_str:
                    bg.blit(text, textRect)
                temp_y = textRect.centery

                jstick_str = ''
                i = 1
                axisread = j.get_axis(i)
                if abs(axisread) > analog_deadzone:
                    axis_y = int(axisread * box_factor)
                    no_buttons_pressed = pygame.time.get_ticks()
                    jstick_str = 'Axis %i reads %.2f' % (i, axisread)
                text = font_text.render(jstick_str, True, WHITE)
                textRect = text.get_rect()
                textRect.centerx = bg.get_rect().centerx
                textRect.centery = temp_y - textRect.height
                if jstick_str:
                    bg.blit(text, textRect)
                pygame.draw.rect(bg, RED, ((screen_centerx - 1) + axis_x, (screen_centery - 1) + axis_y, 3, 3))
                text = font_text.render('Deadzone %.2f' % analog_deadzone, True, WHITE)
                textRect = text.get_rect()
                textRect.left = 5
                textRect.top = 30
                bg.blit(text, textRect)
            else:
                jstick_str = ''
                for i in range(0, j.get_numaxes()):
                    axisread = j.get_axis(i)
                    if abs(axisread) > analog_deadzone:
                        no_buttons_pressed = pygame.time.get_ticks()
                        jstick_str = jstick_str +'\n' + 'Axis %i reads %.2f' % (i, axisread)
                for i in range(0, j.get_numbuttons()):
                    buttonread = j.get_button(i)
                    if buttonread != 0:
                        no_buttons_pressed = pygame.time.get_ticks()
                        jstick_str = jstick_str +'\n' + 'Button %i reads %i' % (i, buttonread)
                if jstick_str:
                    rendered_text = render_textrect(jstick_str, font_text, my_rect, WHITE, surface=None)
                    if rendered_text:
                        bg.blit(rendered_text, my_rect.topleft)
        else:
            # no joystick
            jstick_str = 'no joystick found'
            text = font_text.render(jstick_str, True, WHITE)
            textRect = text.get_rect()
            textRect.centerx = bg.get_rect().centerx
            textRect.centery = bg.get_rect().bottom - textRect.height
            if jstick_str:
                bg.blit(text, textRect)

        bg.set_at((screen_centerx, screen_centery), WHITE)  # draw single pixel dot at center

        screen.blit(bg, (0, 0))
        pygame.display.flip()
        if not ESCAPE_IS_QUIT:
            if time_to_quit <= 0:
                keepGoing = False  # Quit
    pygame.key.set_repeat()


def dumb_system_id():
    f = open('/proc/cpuinfo')
    line = f.readline()  # cheat, only read first line and expect it to be in order....
    f.close()
    if 'JZ4740' in line:
        return a320
    return papk3  # default

##########################################################################


def sinInterpolation(start, end, steps=30):
    values = [start]
    delta = end - start
    for i in range(1, steps):
        n = (pi / 2.0) * (i / float(steps - 1))
        values.append(start + delta * sin(n))
    return values


class RotatingMenu(object):
    def __init__(self, x, y, radius, arc=pi * 2, defaultAngle=0, wrap=False):
        """
        @param x:
            The horizontal center of this menu in pixels.
        
        @param y:
            The vertical center of this menu in pixels.
        
        @param radius:
            The radius of this menu in pixels(note that this is the size of
            the circular path in which the elements are placed, the actual
            size of the menu may vary depending on item sizes.
        @param arc:
            The arc in radians which the menu covers. pi*2 is a full circle.
        
        @param defaultAngle:
            The angle at which the selected item is found.
        
        @param wrap:
            Whether the menu should select the first item after the last one
            or stop.
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.arc = arc
        self.defaultAngle = defaultAngle
        self.wrap = wrap
        
        self.rotation = 0
        self.rotationTarget = 0
        self.rotationSteps = []  # Used for interpolation
        
        self.items = []
        self.selectedItem = None
        self.selectedItemNumber = 0
    
    def addItem(self, item):
        self.items.append(item)
        if len(self.items) == 1:
            self.selectedItem = item
    
    def selectItem(self, itemNumber):
        if self.wrap == True:
            if itemNumber > len(self.items) - 1:
                itemNumber = 0
            if itemNumber < 0:
                itemNumber = len(self.items) - 1
        else:
            itemNumber = min(itemNumber, len(self.items) - 1)
            itemNumber = max(itemNumber, 0)
        
        self.selectedItem.deselect()
        self.selectedItem = self.items[itemNumber]
        self.selectedItem.select()
        
        self.selectedItemNumber = itemNumber
        
        self.rotationTarget = - self.arc * (itemNumber / float(len(self.items) - 1))
        
        self.rotationSteps = sinInterpolation(self.rotation,
                                              self.rotationTarget, 45)
    
    def rotate(self, angle):
        """@param angle: The angle in radians by which the menu is rotated.
        """
        for i in range(len(self.items)):
            item = self.items[i]
            n = i / float(len(self.items) - 1)
            rot = self.defaultAngle + angle + self.arc * n
            
            item.x = self.x + cos(rot) * self.radius
            item.y = self.y + sin(rot) * self.radius
    
    def update(self):
        if len(self.rotationSteps) > 0:
            self.rotation = self.rotationSteps.pop(0)
            self.rotate(self.rotation)
    
    def draw(self, display):
        """@param display: A pyGame display object
        """
        for item in self.items:
            item.draw(display)


class MenuItem(object):
    def __init__(self, text):
        self.text = text
        
        self.defaultColor = (255, 255, 255)
        self.selectedColor = (255, 0, 0)
        self.color = self.defaultColor
        
        self.x = 0
        self.y = 0  # The menu will edit these
        
        self.font = pygame.font.Font(None, 20)
        self.image = self.font.render(self.text, True, self.color)
        size = self.font.size(self.text)
        self.xOffset = size[0] / 2
        self.yOffset = size[1] / 2
    
    def select(self):
        """Just visual stuff"""
        self.color = self.selectedColor
        self.redrawText()
    
    def deselect(self):
        """Just visual stuff"""
        self.color = self.defaultColor
        self.redrawText()
    
    def redrawText(self):
        self.font = pygame.font.Font(None, 20)
        self.image = self.font.render(self.text, True, self.color)
        size = self.font.size(self.text)
        self.xOffset = size[0] / 2
        self.yOffset = size[1] / 2
    
    def draw(self, display):
        display.blit(self.image, (self.x - self.xOffset, self.y - self.yOffset))

##########################################################################


def doit(do_sound_test=False):
    window_res = (480, 272)  # FIXME use device res?
    
    pygame.mixer.init()
    for x in sound_buttons:
        sound_buttons[x] = pygame.mixer.Sound(sound_buttons[x])

    pygame.init()

    # set up the screen/window
    screen = pygame.display.set_mode(window_res)
    pygame.mouse.set_visible(False)
    pygame.display.set_caption("Hardware Test")
    my_rect = screen.get_rect()
    width = my_rect.width
    height = my_rect.height

    # set up fonts
    font_text = pygame.font.SysFont(None, 20)
    font_time = pygame.font.SysFont(None, 40)
    
    clock = pygame.time.Clock()

    try:
        j = pygame.joystick.Joystick(0)
        j.init()
        print 'Initialized Joystick : %s' % j.get_name()
    except pygame.error:
        j = None
    

    #######################
    fps_limit = 90
    menu_mapping = [
        ('Button test', test_buttons),
        ('Analog test', test_analog1),
        ('gsensor test', test_analog2),
        ('Sound test', test_sound),
        #('Mic test', test_mic),
        ('Exit', None),
    ]
    menu = RotatingMenu(x=width / 2, y=height / 2, radius=(min(width, height) / 2) - 20, arc=pi, defaultAngle=pi / 2.0, wrap=True)
    
    for i, menu_entry in enumerate(menu_mapping):
        menu.addItem(MenuItem(menu_entry[0]))
    menu.selectItem(0)
    
    #test_buttons(clock, screen, font_time, font_text)
    
    # Loop
    while True:
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key in [pygame.K_LEFT, pygame.K_UP]:
                    menu.selectItem(menu.selectedItemNumber + 1)
                elif event.key in [pygame.K_RIGHT, pygame.K_DOWN]:
                    menu.selectItem(menu.selectedItemNumber - 1)
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_ESCAPE]:
                    pass
                else:
                    menu_func = menu_mapping[menu.selectedItemNumber][1]
                    if menu_func:
                        menu_func(clock, screen, font_time, font_text, j)
                        menu.selectItem(menu.selectedItemNumber + 1)
                    else:
                        return False  # Quit
        
        # Update stuff
        menu.update()
        
        # Draw stuff
        screen.fill((0, 0, 0))
        menu.draw(screen)
        pygame.display.flip()  # Show the updated scene
        clock.tick(fps_limit)
    
    if j:
        j.quit()

    #pygame.image.save(screen, "screenshot.png")


def main(argv=None):
    if argv is None:
        argv = sys.argv
    
    if len(argv) >= 2:
        do_sound_test = True
    else:
        do_sound_test = False
    doit(do_sound_test=do_sound_test)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
