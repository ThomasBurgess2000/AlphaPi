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
# font = ImageFont.truetype('minecraftia.ttf',8)

outputstring = ""
black = "black"
white = "white"
#FUNCTIONS


location_x = 0

def main(stdscr):
    #stdscr.nodelay(True)
    return stdscr.getch()



while True:
    keypress = curses.wrapper(main)
    #print ("key:", keypress)
    if (keypress <= 255):
        outputstring = outputstring + chr(keypress)
    elif (keypress == 256 or keypress == curses.KEY_BACKSPACE):
        print("backspace entered")
        outputstring = outputstring[:-1]
    draw.rectangle((0,0,width,height),outline=0,fill=black)
    if len(outputstring) < 21:
        draw.text((x, top+0), outputstring, font=font, fill=white)
    elif len(outputstring) < 41:
        draw.text((x, top+0), outputstring[:21], font=font, fill=white)
        draw.text((x, top+8), outputstring[21:], font=font, fill=white)
    elif len(outputstring) < 61:
        draw.text((x, top+0), outputstring[:21], font=font, fill=white)
        draw.text((x, top+8), outputstring[21:41], font=font, fill=white)
        draw.text((x, top+16), outputstring[41:], font=font, fill=white)
    elif len(outputstring) < 81:
        draw.text((x, top+0), outputstring[:21], font=font, fill=white)
        draw.text((x, top+8), outputstring[21:41], font=font, fill=white)
        draw.text((x, top+16), outputstring[41:61], font=font, fill=white)
        draw.text((x, top+25), outputstring[61:], font=font, fill=white)
    elif len(outputstring) >= 81:
        draw.text((x, top+0), outputstring[-80:-60], font=font, fill=white)
        draw.text((x, top+8), outputstring[-60:-40], font=font, fill=white)
        draw.text((x, top+16), outputstring[-40:-20], font=font, fill=white)
        draw.text((x, top+25), outputstring[-20:], font=font, fill=white)
    disp.image(image)
    disp.show()