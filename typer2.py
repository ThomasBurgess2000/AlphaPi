import time
import subprocess
from board import SCL, SDA, D4
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305
import keyboard
import string
import curses

oled_reset = digitalio.DigitalInOut(D4)
i2c = busio.I2C(SCL, SDA)

disp = adafruit_ssd1305.SSD1305_I2C(128, 32, i2c, reset=oled_reset)

# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
 
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
 
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0
 
 
# Load default font.
font = ImageFont.load_default()

string = ""

#FUNCTIONS

key="lol"

def main(stdscr):
    stdscr.nodelay(True)
    return stdscr.getch()



while True:
    keypress = curses.wrapper(main)
    #print ("key:", keypress)
    if (keypress == ord('a')):
        print ("a pressed")
    if (keypress == curses.KEY_RIGHT):
        print ("right pressed")
    
