import os
import pty
import curses
from board import SCL, SDA, D4
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305
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

# deque with maxlen will automatically remove old items when the limit is reached
history = deque(maxlen=2000)
history.append(">")
scroll = 0
max_scroll = 0


def wrap_text(text, width):
    # Split the text by spaces to get words
    words = text.split(' ')
    lines = []
    line = ''

    for word in words:
        if len(line + ' ' + word) <= width:
            line += ' ' + word
        else:
            lines.append(line.strip())  # Strip leading and trailing spaces
            line = word

    # Add any leftover text
    if line != '':
        lines.append(line.strip())  # Strip leading and trailing spaces

    return lines


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
    master, slave = pty.openpty()

    pid = os.fork()
    if pid == 0:  # Child process
        # Replaces the current process with the bash shell
        os.execv('/bin/bash', ['/bin/bash'])
    else:  # Parent process
        while True:
            output = os.read(master, 1024).decode('utf-8')
            wrapped_output = wrap_text(output, 20)

            # Add output to history, with line wrapping
            for line in wrapped_output:
                history.append(line)

            max_scroll = len(history) - 3 if len(history) > 3 else 0
            scroll = max_scroll
            draw_text()

            c = stdscr.getch()
            if c == 10:  # ENTER
                os.write(master, bytes(input_str + '\n', 'utf-8'))
                input_str = ""
            elif c == 259:  # UP ARROW
                os.write(master, bytes('\033[A', 'utf-8'))
            elif c == 258:  # DOWN ARROW
                os.write(master, bytes('\033[B', 'utf-8'))
            elif c == 256 or c == curses.KEY_BACKSPACE:
                input_str = input_str[:-1]
                os.write(master, bytes('\x7f', 'utf-8'))  # DEL character
            else:
                if 32 <= c <= 126:  # Check if c is a printable ASCII character
                    input_str += chr(c)
                    os.write(master, bytes(chr(c), 'utf-8'))


if __name__ == "__main__":
    curses.wrapper(terminal)
