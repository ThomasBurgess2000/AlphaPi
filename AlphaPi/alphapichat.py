import time
import subprocess
from board import SCL, SDA, D4
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305
import curses
import sys
import openai
from collections import deque

# Initialize the OLED display
oled_reset = digitalio.DigitalInOut(D4)
i2c = busio.I2C(SCL, SDA)
disp = adafruit_ssd1305.SSD1305_I2C(128, 32, i2c, reset=oled_reset)
width = disp.width
height = disp.height

# Drawing objects
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

# Set your OpenAI API key here
openai.api_key = 'your-api-key'

# deque with maxlen will automatically remove old items when the limit is reached
history = deque(maxlen=10)
history.append(">")

# Scrolling variables
scroll = 0
max_scroll = 0

# Function for ChatGPT API


def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message["content"]


def draw_text():
    global scroll
    global max_scroll

    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Draw up to 4 lines of history
    for i in range(4):
        if scroll + i < len(history):
            draw.text((0, 8*i), history[scroll + i], font=font, fill=255)

    disp.image(image)
    disp.show()


def terminal(stdscr):
    global history
    global scroll
    global max_scroll

    input_str = ""
    draw_text()

    while True:
        c = stdscr.getch()

        # ENTER
        if c == 10:
            if input_str.strip() != "":
                history.append(input_str)
                resp = get_completion(input_str)
                history.append("A> " + resp)
                input_str = ""
                max_scroll = len(history) - 4 if len(history) > 4 else 0
                scroll = max_scroll
        # BACKSPACE
        elif c == 8 or c == 127:
            input_str = input_str[:-1]
        # UP ARROW
        elif c == 259:
            if scroll > 0:
                scroll -= 1
        # DOWN ARROW
        elif c == 258:
            if scroll < max_scroll:
                scroll += 1
        else:
            input_str += chr(c)

        history[-1] = ">" + input_str
        draw_text()


if __name__ == "__main__":
    curses.wrapper(terminal)
