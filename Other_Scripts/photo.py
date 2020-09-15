import os
import time
import random
import subprocess
from board import SCL, SDA, D4
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305

oled_reset = digitalio.DigitalInOut(D4)
i2c = busio.I2C(SCL,SDA)
disp = adafruit_ssd1305.SSD1305_I2C(128,32,i2c,reset=oled_reset)

#Clear display
disp.fill(0)
disp.show()

width = disp.width
height = disp.height
image = Image.new("1",(width,height))
draw = ImageDraw.Draw(image)

padding = -2
top = padding
bottom = height - padding
x = 0

draw.rectangle((0,0,width,height),outline=0,fill=0)
image = Image.open(r'/home/pi/oled_bonnet/oled_bonnet/ninjinka.png')
image = image.convert('1')
disp.image(image)
disp.show()
	
