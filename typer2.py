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

#The version of the string that is saved to file
outputstring = ""
#The version of the string that is displayed
copy_of_output = ""
black = "black"
white = "white"
#FUNCTIONS

modifier = 0
every_21 = 0

location_x = 0

def main(stdscr):
    #stdscr.nodelay(True)
    print(len(copy_of_output))
    return stdscr.getch()

def fontchooser():
    return ("Nothing")

def linewriter(copy_of_output):
    # Trying to allow for line breaks
    string_adj_len = len(copy_of_output)
    if string_adj_len <= 21:
        draw.text((x, top+0), copy_of_output, font=font, fill=white)
    elif string_adj_len <= 42:
        draw.text((x, top+0), copy_of_output[:21], font=font, fill=white)
        draw.text((x, top+8), copy_of_output[21:], font=font, fill=white)
    elif string_adj_len <= 63:
        draw.text((x, top+0), copy_of_output[:21], font=font, fill=white)
        draw.text((x, top+8), copy_of_output[21:42], font=font, fill=white)
        draw.text((x, top+16), copy_of_output[42:], font=font, fill=white)
    # Changes distance from top to prevent last line from going off of screen
    elif string_adj_len <= 84:
        draw.text((x, top-2), copy_of_output[:21], font=font, fill=white)
        draw.text((x, top+6), copy_of_output[21:42], font=font, fill=white)
        draw.text((x, top+14), copy_of_output[42:63], font=font, fill=white)
        draw.text((x, top+23), copy_of_output[63:], font=font, fill=white)
    elif string_adj_len > 84:
        draw.text((x, top-2), copy_of_output[-84:-63], font=font, fill=white)
        draw.text((x, top+6), copy_of_output[-63:-42], font=font, fill=white)
        draw.text((x, top+14), copy_of_output[-42:-21], font=font, fill=white)
        draw.text((x, top+23), copy_of_output[-21:], font=font, fill=white)

while True:
    
    keypress = curses.wrapper(main)
    #print ("key:", keypress)
    if (keypress <= 255):
        outputstring = outputstring + chr(keypress)
        copy_of_output = copy_of_output + chr(keypress)
    elif (keypress == 256 or keypress == curses.KEY_BACKSPACE):
        outputstring = outputstring[:-1]
        copy_of_output = copy_of_output[:-1]
        if len(copy_of_output) % 21 == 0 and len(copy_of_output) >= 84:
            copy_of_output = copy_of_output[:-21]
    elif (keypress == curses.ENTER):
        outputstring = outputstring + "\n"
        if len(copy_of_output) <= 21:
            modifier = 21 - len(copy_of_output)
        else:
            modifier = len(copy_of_output)%21
        i = 0
        while i < modifier:
            copy_of_output = copy_of_output + " "
            i += 1
    if len(copy_of_output) % 21 == 0 and len(copy_of_output) >= 84:
        copy_of_output = copy_of_output + "                     "
    draw.rectangle((0,0,width,height),outline=0,fill=black)
    
    linewriter(copy_of_output)
    disp.image(image)
    disp.show()