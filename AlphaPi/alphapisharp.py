import time
import subprocess
import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont

import keyboard
import string
import curses


# 400x240 Sharp Memory disp
import adafruit_sharpmemorydisp
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
scs = digitalio.DigitalInOut(board.D6)
disp = adafruit_sharpmemorydisp.SharpMemorydisp(spi, scs, 400, 240)
print("Filling white")
disp.fill(1)
disp.show()
print("done")
FONTSIZE = 42
#font = ImageFont.truetype("usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONTSIZE)
font = ImageFont.truetype("RobotoMono.ttf", FONTSIZE)

# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
BLACK = 0
WHITE = 255

# Splash screen (removed until get image with correct dimensions)
# image = Image.open(r'piskel.png')
# image = image.convert('1')
# disp.image(image)
# disp.show()
# time.sleep(3)

image = Image.new('1', (width, height))
 
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=WHITE, fill=WHITE)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


#The version of the string that is saved to file
outputstring = ""
#The version of the string that is disped
copy_of_output = ""
black = "black"
white = "white"
#FUNCTIONS

modifier = 0
every_21 = 0

location_x = 0

first_line = 16
second_line = 32
third_line = 48
fourth_line = 64
fifth_line = 80
sixth_line = 96
line_height = 35


def main(stdscr):
    #stdscr.nodelay(True)
    print("disp output: " + copy_of_output + "\n")
    print("Saved output: " + outputstring + "\n")
    return stdscr.getch()

def fontchooser():
    return ("Nothing")

def linewriter(copy_of_output,string_adj_len):
  
    # if string_adj_len <= first_line:
    #     draw.text((x, top+0), copy_of_output, font=font, fill=black)
    # elif string_adj_len <= second_line:
    #     draw.text((x, top+0), copy_of_output[:first_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)), copy_of_output[first_line:], font=font, fill=black)
    # elif string_adj_len <= third_line:
    #     draw.text((x, top+0), copy_of_output[:first_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)), copy_of_output[first_line:second_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*2), copy_of_output[second_line:], font=font, fill=black)
    # # Changes distance from top to prevent last line from going off of screen
    # elif string_adj_len <= fourth_line:
    #     draw.text((x, top+0), copy_of_output[:first_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)), copy_of_output[first_line:second_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*2), copy_of_output[second_line:third_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*3), copy_of_output[third_line:], font=font, fill=black)
    # elif string_adj_len <= fifth_line:
    #     draw.text((x, top+0), copy_of_output[:first_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)), copy_of_output[first_line:second_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*2), copy_of_output[second_line:third_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*3), copy_of_output[third_line:fourth_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*4), copy_of_output[fourth_line:], font=font, fill=black)
    # elif string_adj_len <= sixth_line:
    #     draw.text((x, top+0), copy_of_output[:first_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)), copy_of_output[first_line:second_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*2), copy_of_output[second_line:third_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*3), copy_of_output[third_line:fourth_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*4), copy_of_output[fourth_line:fifth_line], font=font, fill=black)
    #     draw.text((x, top+(line_height)*5), copy_of_output[fifth_line:], font=font, fill=black)

    disp.fill(1)
    disp.text(" hello world!", 0, 0, 0)
    disp.text(" This is the", 0, 8, 0)
    disp.text(" CircuitPython", 0, 16, 0)
    disp.text("adafruit library", 0, 24, 0)
    disp.text(" for the SHARP", 0, 32, 0)
    disp.text(" Memory disp :) ", 0, 40, 0)
    disp.show()
    disp.fill(1)
    disp.text("this is testing the refresh!", 0, 0, 0)
    disp.text("REFRESH", 0, 8, 0)
    disp.text("REFRESH", 0, 16, 0)
    disp.text("REFRESH", 0, 24, 0)
    disp.text("REFRESH", 0, 32, 0)
    disp.text("REFRESH", 0, 40, 0)
    disp.show()

while True:
    # This is the section that logs keypresses for the whole running of the program...might need to move it to a separate section though if line_writer becomes its own "app"
    keypress = curses.wrapper(main)
    #print ("key:", keypress)
    if (keypress == curses.KEY_ENTER or keypress == 10 or keypress == 13):
        outputstring = outputstring + "\n"
        if len(copy_of_output) <= first_line:
            modifier = first_line - len(copy_of_output)
        else:
            modifier = first_line - (len(copy_of_output)%first_line)
        i = 0
        while i < modifier:
            copy_of_output = copy_of_output + " "
            print (i)
            i += 1
    elif (keypress <= 255):
        outputstring = outputstring + chr(keypress)
        copy_of_output = copy_of_output + chr(keypress)
    elif (keypress == 256 or keypress == curses.KEY_BACKSPACE):
        outputstring = outputstring[:-1]
        copy_of_output = copy_of_output[:-1]
        if ((len(copy_of_output)//first_line-1) - (len(copy_of_output) % first_line-1)) == 1:
            copy_of_output = copy_of_output.rstrip()
    draw.rectangle((0,0,width,height),outline=0,fill=white)
    if (len(copy_of_output)>sixth_line):
        copy_of_output = copy_of_output[first_line:]
    linewriter(copy_of_output,len(copy_of_output))
    disp.image(image)
    disp.show()