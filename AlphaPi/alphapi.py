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

# Splash screen
image = Image.open(r'piskel.png')
image = image.convert('1')
disp.image(image)
disp.show()
time.sleep(3)

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


modifier = 0

#FUNCTIONS

def main(stdscr):
    # stdscr.nodelay(True)
    # print("Display output: " + copy_of_output + "\n")
    # print("Saved output: " + outputstring + "\n")
    return stdscr.getch()

def fontchooser():
    return ("Nothing")

def linewriter(copy_of_output,string_adj_len):
  
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

def wordprocessor_main():
    global outputstring
    global copy_of_output
    global modifier
    
    while True:
        # This is the section that logs keypresses for the whole running of the program...might need to move it to a separate section though if line_writer becomes its own "app"
        keypress = curses.wrapper(main)
        #print ("key:", keypress)
        if (keypress == curses.KEY_ENTER or keypress == 10 or keypress == 13):
            outputstring = outputstring + "\n"
            if len(copy_of_output) <= 21:
                modifier = 21 - len(copy_of_output)
            else:
                modifier = 21- (len(copy_of_output)%21)
            i = 0
            while i < modifier:
                copy_of_output = copy_of_output + " "
                print (i)
                i += 1
        elif (keypress <= 31):
            if (keypress == 27):
                return
        elif (keypress <= 255):
            outputstring = outputstring + chr(keypress)
            copy_of_output = copy_of_output + chr(keypress)
        elif (keypress == 256 or keypress == curses.KEY_BACKSPACE):
            outputstring = outputstring[:-1]
            copy_of_output = copy_of_output[:-1]
            if ((len(copy_of_output)//20) - (len(copy_of_output) % 20)) == 1:
                copy_of_output = copy_of_output.rstrip()
        draw.rectangle((0,0,width,height),outline=0,fill=black)
        if (len(copy_of_output)>84):
            copy_of_output = copy_of_output[21:]
        linewriter(copy_of_output,len(copy_of_output))
        disp.image(image)
        disp.show()
        
def main_menu():
    quit = False
    while quit==False:
        draw.rectangle((0,0,width,height),outline=0,fill=black)
        draw.text((x, top+0), "1. Word Processor", font=font, fill=white)
        draw.text((x, top+8), "2. Backup Files", font=font, fill=white)
        draw.text((x, top+16), "3. Quit", font=font, fill=white)
        disp.image(image)
        disp.show()
        keypress = curses.wrapper(main)
        if (keypress == 49):
            wordprocessor_main()
        elif(keypress == 50):
            backup_files()
        elif(keypress == 51):
            quit == True
    sys.exit(0)

# Start
main_menu()