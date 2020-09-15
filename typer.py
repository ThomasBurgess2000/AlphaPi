import time
import subprocess
from board import SCL, SDA, D4
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305
import keyboard
import string
import threading, time
import getch

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

def thread1():
    global key
    lock = threading.Lock()
    while True:
        with lock:
            key = getch.getch()

def thread2():
    counter = 0
    print ("thread2 started")
    while True:
        draw.rectangle((0,0,width,height),outline=0, fill=0)
        draw.text((x,top+0), str(counter), font=font, fill=255)
        disp.image(image)
        disp.show()
        counter = counter + 1

procThread2 = threading.Thread(target = thread2)
procThread2.daemon = True
procThread1 = threading.Thread(target = thread1)
procThread1.daemon = True
procThread2.start()
procThread1.start()

while True:
    print(key)
