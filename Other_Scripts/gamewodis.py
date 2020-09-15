import os
import pygame
import time
import random
import subprocess
from board import SCL, SDA, D4
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305
from pygame.locals import *

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame.display
pygame.display.init()


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

font = ImageFont.load_default()

#Pygame

location_x = 0

running = True
while running:
	pressed_keys = pygame.key.get_pressed()
	if pressed_keys[K_RIGHT]:
		location_x += 1
	if pressed_keys[K_LEFT]:
		location_x -= 1
	if pressed_keys[K_ESCAPE]:
		pygame.quit()
	pygame.event.pump()
	draw.rectangle((0,0,width,height),outline=0,fill=0)
	draw.point((location_x, 5), fill="white")
	disp.image(image)
	disp.show()
	
