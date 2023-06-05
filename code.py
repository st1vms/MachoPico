import os
import time
import board
import digitalio
import usb_hid
import busio
import displayio
import terminalio
import adafruit_displayio_ssd1306
from adafruit_display_text import label
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_it import KeyboardLayout
from adafruit_hid.keycode import Keycode

PASSWORD_FOLDER = "pwd"

POLL_RATE = 0.2

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32
MAX_VISIBLE_CHARACTERS = 10

CURRENT_TEXT_INDEX = 0

kb = Keyboard(usb_hid.devices)
layout = KeyboardLayout(kb)

displayio.release_displays()

i2c = busio.I2C(scl=board.GP1, sda=board.GP0)

display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(
    display_bus, width=SCREEN_WIDTH, height=SCREEN_HEIGHT
)
text_group = displayio.Group(scale=2)


def setup_text_area(text: str, text_area: label.Label = None) -> label.Label:
    if text_area == None:
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    else:
        text_area.text = text

    if len(text) > MAX_VISIBLE_CHARACTERS:
        text_area.anchor_point = (0.5, 0.4)
        text_area.anchored_position = (SCREEN_WIDTH / 1.5, SCREEN_HEIGHT / 4)
    else:
        text_area.anchor_point = (0, 0.4)
        text_area.anchored_position = (0, SCREEN_HEIGHT / 4)

    return text_area


text_area = setup_text_area("MACHO PICO")
text_group.append(text_area)

display.show(text_group)

# Process Text folder

PWD_STORE = {}

for file in os.listdir(PASSWORD_FOLDER):
    fname = file.split(".")[0]
    with open(f"{PASSWORD_FOLDER}/{file}", "r") as fp:
        PWD_STORE[fname] = fp.read().rstrip()

PWD_STORE = dict(sorted(PWD_STORE.items(), key=lambda x: x[0][0].lower()))
PWD_KEYS = list(sorted(PWD_STORE.keys(), key=lambda x: x[0].lower()))
print(PWD_KEYS)

time.sleep(2)

left_button = digitalio.DigitalInOut(board.GP5)
left_button.direction = digitalio.Direction.INPUT


def left_button_routine():
    global CURRENT_TEXT_INDEX

    if CURRENT_TEXT_INDEX == 0:
        CURRENT_TEXT_INDEX = len(PWD_KEYS) - 1
    else:
        CURRENT_TEXT_INDEX -= 1



central_button = digitalio.DigitalInOut(board.GP9)
central_button.direction = digitalio.Direction.INPUT

def press_enter():
    kb.press(Keycode.SHIFT)
    kb.press(Keycode.ENTER)
    kb.release_all()

def central_button_routine():
    
    _stop_condition = 0

    global CURRENT_TEXT_INDEX
    _text = PWD_STORE[PWD_KEYS[CURRENT_TEXT_INDEX]].split('\n')
    for line in _text:
        if line:
            for ch in line:
                if not central_button.value:
                    _stop_condition = 1
                
                if _stop_condition and (left_button.value or right_button.value):
                    return
                try:
                    layout.write(ch)
                except ValueError as e:
                    pass
                
               
                
        press_enter()

right_button = digitalio.DigitalInOut(board.GP13)
right_button.direction = digitalio.Direction.INPUT


def righ_button_routine():
    global CURRENT_TEXT_INDEX

    if CURRENT_TEXT_INDEX == len(PWD_KEYS) - 1:
        CURRENT_TEXT_INDEX = 0
    else:
        CURRENT_TEXT_INDEX += 1


current_text = PWD_KEYS[CURRENT_TEXT_INDEX]
text_area = setup_text_area(current_text, text_area=text_area)
is_pressing = False
slide_counter = 0
while True:
    time.sleep(POLL_RATE)

    v = (left_button.value, central_button.value, right_button.value)

    if v[0] and not any((v[1], v[2])):
        if not is_pressing:
            is_pressing = True
            left_button_routine()
            current_text = PWD_KEYS[CURRENT_TEXT_INDEX]
            text_area = setup_text_area(current_text, text_area=text_area)
    elif v[1] and not any((v[0], v[2])):
        if not is_pressing:
            is_pressing = True
            text_area = setup_text_area("Typing...", text_area=text_area)
            central_button_routine()
            current_text = PWD_KEYS[CURRENT_TEXT_INDEX]
            text_area = setup_text_area(current_text, text_area=text_area)
    elif v[2] and not any((v[0], v[1])):
        if not is_pressing:
            is_pressing = True
            righ_button_routine()
            current_text = PWD_KEYS[CURRENT_TEXT_INDEX]
            text_area = setup_text_area(current_text, text_area=text_area)
    else:
        is_pressing = False

    if len(current_text) > MAX_VISIBLE_CHARACTERS:
        if slide_counter < len(current_text):
            text_area.text = text_area.text + "  "
            slide_counter += 1
        else:
            slide_counter = 0
            text_area.text = current_text
