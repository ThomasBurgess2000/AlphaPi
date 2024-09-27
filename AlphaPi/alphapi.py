import time
import sys
import curses
from os import listdir, path

import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1305

# Constants
OLED_WIDTH = 128
OLED_HEIGHT = 32
SPLASH_IMAGE_PATH = 'piskel.png'
FONT_PATH = 'minecraftia.ttf'  # Ensure this font exists or use default
FONT_SIZE = 8
MAX_FILENAME_LENGTH = 42  # Allow two lines of filename display
MAX_DISPLAY_LINES = 3      # Number of lines visible on OLED

# Initialize OLED display
oled_reset = digitalio.DigitalInOut(board.D4)
i2c = busio.I2C(board.SCL, board.SDA)
disp = adafruit_ssd1305.SSD1305_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, reset=oled_reset)

# Initialize image buffer
image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT))
draw = ImageDraw.Draw(image)

# Load font
try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
except IOError:
    font = ImageFont.load_default()

# Colors
BLACK = 0
WHITE = 1

# Key codes
ESCAPE = 27
ENTER_KEYS = [10, 13, curses.KEY_ENTER]

def display_image():
    """Update the OLED display with the current image buffer."""
    disp.image(image)
    disp.show()

def clear_display():
    """Clear the OLED display."""
    draw.rectangle((0, 0, OLED_WIDTH, OLED_HEIGHT), outline=BLACK, fill=BLACK)

def show_splash_screen():
    """Display a splash screen on the OLED."""
    try:
        splash = Image.open(SPLASH_IMAGE_PATH).convert('1')
        splash = splash.resize((OLED_WIDTH, OLED_HEIGHT))
        disp.image(splash)
        disp.show()
        time.sleep(2)
    except Exception as e:
        # If splash image not found, just clear the display
        clear_display()
        display_image()

def line_writer(text):
    """
    Writes text to the OLED display, handling line wrapping and scrolling.
    Only updates the display if the content has changed to prevent flickering.
    """
    if not hasattr(line_writer, "previous_text"):
        line_writer.previous_text = None

    if text == line_writer.previous_text:
        return  # No change, no need to update

    clear_display()

    # Split the text into lines based on '\n'
    raw_lines = text.split('\n')
    lines = []
    max_chars_per_line = 21  # Adjust based on font size and OLED width

    for raw_line in raw_lines:
        # Handle word wrapping for each line
        while len(raw_line) > max_chars_per_line:
            # Attempt to wrap at the last space within max_chars_per_line
            wrap_at = raw_line.rfind(' ', 0, max_chars_per_line)
            if wrap_at == -1:
                wrap_at = max_chars_per_line
            lines.append(raw_line[:wrap_at])
            raw_line = raw_line[wrap_at:].lstrip()
        lines.append(raw_line)

    # Display the last three lines for scrolling effect
    display_lines = lines[-MAX_DISPLAY_LINES:]

    for idx, line in enumerate(display_lines):
        y = idx * (FONT_SIZE + 2)
        draw.text((0, y), line, font=font, fill=WHITE)

    display_image()
    line_writer.previous_text = text

def main(stdscr):
    """Main function to initialize the application."""
    # Initialize curses
    curses.curs_set(0)          # Hide cursor
    stdscr.nodelay(True)        # Non-blocking input
    stdscr.keypad(True)

    show_splash_screen()
    main_menu(stdscr)

def main_menu(stdscr):
    """Display the main menu with options to start the word processor or quit."""
    while True:
        clear_display()
        menu_text = "1. Word Processor\n2. Quit"
        for idx, line in enumerate(menu_text.split('\n')):
            draw.text((0, idx * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == ord('1'):
            wordprocessor_menu(stdscr)
        elif key == ord('2') or key == ESCAPE:
            clear_display()
            display_image()
            sys.exit(0)
        time.sleep(0.05)  # Small delay to prevent high CPU usage

def wordprocessor_menu(stdscr):
    """Display the word processor menu with options to create, edit, or get help."""
    while True:
        clear_display()
        menu_text = "1. Create New File\n2. Edit Existing File\n3. Help\nEsc. Back"
        lines = menu_text.split('\n')
        for idx, line in enumerate(lines):
            draw.text((0, idx * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == ord('1'):
            filename = get_filename(stdscr, "Create New File")
            if filename:
                wordprocessor_edit(stdscr, filename, new=True)
        elif key == ord('2'):
            filename = select_file(stdscr)
            if filename:
                wordprocessor_edit(stdscr, filename, new=False)
        elif key == ord('3'):
            show_help(stdscr)
        elif key == ESCAPE:
            return
        time.sleep(0.05)

def get_filename(stdscr, prompt):
    """
    Prompts the user to enter a filename.
    """
    filename = ""
    while True:
        clear_display()
        draw.text((0, 0), prompt, font=font, fill=WHITE)
        draw.text((0, FONT_SIZE + 2), filename, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key in ENTER_KEYS:
            if filename:
                return filename
        elif key == ESCAPE:
            return None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            filename = filename[:-1]
        elif 32 <= key <= 126 and len(filename) < MAX_FILENAME_LENGTH:
            filename += chr(key)

def select_file(stdscr):
    """
    Displays a list of existing text files and allows the user to select one.
    """
    files = [f for f in listdir('.') if path.isfile(f) and f.endswith('.txt')]
    if not files:
        clear_display()
        draw.text((0, 0), "No .txt files found.", font=font, fill=WHITE)
        display_image()
        time.sleep(1)
        return None

    current_selection = 0
    visible_files = files[:3]  # Display up to 3 files

    while True:
        clear_display()
        draw.text((0, 0), "Select a file:", font=font, fill=WHITE)
        for idx, filename in enumerate(visible_files):
            if idx == current_selection:
                line = "> " + filename
            else:
                line = "  " + filename
            draw.text((0, (idx + 1) * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(visible_files)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(visible_files)
        elif key in ENTER_KEYS:
            if files:
                return visible_files[current_selection]
        elif key == ESCAPE:
            return None
        time.sleep(0.05)

def show_help(stdscr):
    """Display the help information."""
    help_text = (
        "Word Processor Help\n"
        "Use arrow keys to navigate.\n"
        "Type to enter text.\n"
        "Enter to confirm.\n"
        "Esc to save and exit."
    )
    clear_display()
    lines = help_text.split('\n')
    for idx, line in enumerate(lines):
        draw.text((0, idx * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
    display_image()
    while True:
        key = stdscr.getch()
        if key == ESCAPE:
            return
        time.sleep(0.05)

def wordprocessor_edit(stdscr, filename, new=False):
    """
    Edits the given file. If new=True, starts with empty content.
    """
    outputstring = ""
    if not new and path.exists(filename):
        with open(filename, 'r') as f:
            outputstring = f.read()

    while True:
        # Only update the display if there's a change
        line_writer(outputstring)

        key = stdscr.getch()
        if key in ENTER_KEYS:
            outputstring += '\n'
        elif key == ESCAPE:
            # Save the file before exiting
            try:
                with open(filename, 'w') as f:
                    f.write(outputstring)
            except Exception as e:
                # Optionally, display an error message
                clear_display()
                draw.text((0, 0), "Error saving file.", font=font, fill=WHITE)
                display_image()
                time.sleep(1)
            return
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            outputstring = outputstring[:-1]
        elif 32 <= key <= 126:
            outputstring += chr(key)
        # No need to sleep here; loop is already fast enough

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        clear_display()
        display_image()
        sys.exit(0)
