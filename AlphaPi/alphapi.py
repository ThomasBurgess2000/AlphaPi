import time
import sys
import curses
from os import listdir, path
from openai import OpenAI
import threading
import json

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
CONFIG_FILE = 'alphachat_config.json'  # Configuration file path

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

# Global Variables for AlphaChat
alpha_chat_api_key = ""
alpha_chat_model = "gpt-4o-mini"  # Default model
chat_history = []
chat_lock = threading.Lock()

# Initialize OpenAI client as None at global scope
client = None


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

def line_writer(text, scroll_offset=0):
    """
    Writes text to the OLED display, handling line wrapping and scrolling.
    Only updates the display if the content has changed to prevent flickering.
    """
    if not hasattr(line_writer, "previous_text"):
        line_writer.previous_text = None
    if not hasattr(line_writer, "previous_scroll"):
        line_writer.previous_scroll = 0

    if text == line_writer.previous_text and scroll_offset == line_writer.previous_scroll:
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

    # Apply scroll offset
    display_lines = lines[scroll_offset:scroll_offset + MAX_DISPLAY_LINES]

    for idx, line in enumerate(display_lines):
        y = idx * (FONT_SIZE + 2)
        draw.text((0, y), line, font=font, fill=WHITE)

    display_image()
    line_writer.previous_text = text
    line_writer.previous_scroll = scroll_offset

def load_config():
    """Load configuration from the CONFIG_FILE if it exists."""
    global alpha_chat_api_key, alpha_chat_model, client
    if path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                alpha_chat_api_key = config.get("api_key", "")
                alpha_chat_model = config.get("model", "gpt-4o-mini")
                # Initialize the OpenAI client with the API key
                client = OpenAI(api_key=alpha_chat_api_key)
        except Exception as e:
            # If there's an error reading the config, proceed with defaults
            alpha_chat_api_key = ""
            alpha_chat_model = "gpt-4o-mini"
            client = OpenAI(api_key=alpha_chat_api_key)  # Initialize with empty API key
    else:
        # Config file does not exist, proceed with defaults
        alpha_chat_api_key = ""
        alpha_chat_model = "gpt-4o-mini"
        client = OpenAI(api_key=alpha_chat_api_key)  # Initialize with empty API key


def save_config():
    """Save current configuration to the CONFIG_FILE."""
    config = {
        "api_key": alpha_chat_api_key,
        "model": alpha_chat_model
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        # Optionally, handle errors (e.g., display a message)
        pass

def main(stdscr):
    """Main function to initialize the application."""
    # Initialize curses
    curses.curs_set(0)          # Hide cursor
    stdscr.nodelay(True)        # Non-blocking input
    stdscr.keypad(True)

    load_config()  # Load existing configuration
    show_splash_screen()
    main_menu(stdscr)

def main_menu(stdscr):
    """Display the main menu with options to start Word Processor, AlphaChat, or quit."""
    menu_options = ["Word Processor", "AlphaChat", "Quit"]
    current_selection = 0

    while True:
        clear_display()
        for idx, option in enumerate(menu_options):
            if idx == current_selection:
                line = "> " + option
            else:
                line = "  " + option
            draw.text((0, idx * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(menu_options)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(menu_options)
        elif key in ENTER_KEYS:
            if menu_options[current_selection] == "Word Processor":
                wordprocessor_menu(stdscr)
            elif menu_options[current_selection] == "AlphaChat":
                alphachat_menu(stdscr)
            elif menu_options[current_selection] == "Quit":
                clear_display()
                display_image()
                sys.exit(0)
        time.sleep(0.05)  # Small delay to prevent high CPU usage

def wordprocessor_menu(stdscr):
    """Display the word processor menu with options to create, edit, or get help."""
    menu_options = ["Create New File", "Edit Existing File", "Help", "Back"]
    current_selection = 0

    while True:
        clear_display()
        for idx, option in enumerate(menu_options):
            if idx == current_selection:
                line = "> " + option
            else:
                line = "  " + option
            draw.text((0, idx * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(menu_options)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(menu_options)
        elif key in ENTER_KEYS:
            if menu_options[current_selection] == "Create New File":
                filename = get_filename(stdscr, "Create New File")
                if filename:
                    wordprocessor_edit(stdscr, filename, new=True)
            elif menu_options[current_selection] == "Edit Existing File":
                filename = select_file(stdscr)
                if filename:
                    wordprocessor_edit(stdscr, filename, new=False)
            elif menu_options[current_selection] == "Help":
                show_help(stdscr)
            elif menu_options[current_selection] == "Back":
                return
        time.sleep(0.05)

def alphachat_menu(stdscr):
    """Display the AlphaChat menu with options to New Chat, Enter API Key, Select Model, or Back."""
    global client
    menu_options = ["New Chat", "Enter API Key", "Select Model", "Back"]
    current_selection = 0

    while True:
        clear_display()
        for idx, option in enumerate(menu_options):
            if idx == current_selection:
                line = "> " + option
            else:
                line = "  " + option
            draw.text((0, idx * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(menu_options)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(menu_options)
        elif key in ENTER_KEYS:
            if menu_options[current_selection] == "New Chat":
                if not alpha_chat_api_key:
                    prompt_api_key(stdscr)
                alphachat_new_chat(stdscr)
            elif menu_options[current_selection] == "Enter API Key":
                prompt_api_key(stdscr)
            elif menu_options[current_selection] == "Select Model":
                select_alphachat_model(stdscr)
            elif menu_options[current_selection] == "Back":
                return
        time.sleep(0.05)

def prompt_api_key(stdscr):
    """Prompt the user to enter the OpenAI API Key."""
    global alpha_chat_api_key
    api_key = ""
    while True:
        clear_display()
        prompt = "Enter API Key:"
        draw.text((0, 0), prompt, font=font, fill=WHITE)
        draw.text((0, FONT_SIZE + 2), api_key, font=font, fill=WHITE)  # Display input unmasked
        display_image()

        key = stdscr.getch()
        if key in ENTER_KEYS:
            if api_key:
                alpha_chat_api_key = api_key
                client.api_key = alpha_chat_api_key
                save_config()  # Save updated API key
                return
        elif key == ESCAPE:
            return
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            api_key = api_key[:-1]
        elif 32 <= key <= 126 and len(api_key) < 128:
            api_key += chr(key)

def select_alphachat_model(stdscr):
    """Allow the user to select the ChatGPT model."""
    global alpha_chat_model
    models = ["gpt-4o-mini", "gpt-4o"]
    current_selection = models.index(alpha_chat_model) if alpha_chat_model in models else 0

    while True:
        clear_display()
        draw.text((0, 0), "Select Model:", font=font, fill=WHITE)
        for idx, model in enumerate(models):
            if idx == current_selection:
                line = "> " + model
            else:
                line = "  " + model
            draw.text((0, (idx + 1) * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(models)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(models)
        elif key in ENTER_KEYS:
            alpha_chat_model = models[current_selection]
            save_config()  # Save updated model
            return
        elif key == ESCAPE:
            return
        time.sleep(0.05)

def alphachat_new_chat(stdscr):
    """Handle the new chat session with ChatGPT."""

    global client

    if not alpha_chat_api_key:
        prompt_api_key(stdscr)
        if not alpha_chat_api_key:
            return  # API Key not set

    # Define the system message
    system_message = (
        "Intellectual Depth: Respond with high-IQ insights, focusing on sharp, critical analysis. "
        "Show a deep appreciation for capitalism and disdain for socialism.\n\n"
        "Agency-Driven, Low-Ego: Empower my decisions with pragmatic, actionable advice. "
        "Keep responses solution-oriented and focused on maximizing my autonomy without undermining my instincts.\n\n"
        "Strong Writing: Deliver responses with articulate, concise, and impactful language. "
        "Prioritize precision over verbosity. Don't hedge when you fear the answer is not politically correct.\n\n"
        "Risk Tolerance: Don’t shy away from high-risk, high-reward strategies. "
        "Offer clear pros and cons but be bold with suggestions, reflecting my preference for calculated risks over overly cautious moves.\n\n"
        "Workaholic Support: Anticipate a high-functioning, productivity-driven environment. "
        "Respond quickly with laser focus, ensuring recommendations enhance my efficiency and output.\n\n"
        "Low-Trust, High Agency: Assume I prefer to verify information myself and provide me with tools to question conventional wisdom. "
        "Offer recommendations that emphasize self-reliance, skepticism of mainstream narratives, and alternatives that maximize my control over outcomes.\n\n"
        "Theological Alignment: When relevant, ground moral or philosophical discussions in principles aligned with Presbyterian Church in America (PCA) theology, avoiding unnecessary ambiguity in matters of faith."
    )

    # Initialize chat history with the system message
    chat_history = [{"role": "system", "content": system_message}]

    user_input = ""
    response_lines = []
    scroll_offset = 0
    is_streaming = False
    stop_stream = False

    def stream_response():
        nonlocal response_lines, scroll_offset, is_streaming, stop_stream
        try:
            response = client.chat.completions.create(
                model=alpha_chat_model,
                messages=chat_history,
                stream=True
            )
            collected_response = ""
            for chunk in response:
                if stop_stream:
                    break
                delta = chunk.choices[0].delta
                if delta.content:
                    collected_response += delta.content
                    with chat_lock:
                        # Split the new content into lines if necessary
                        new_content = delta.content
                        for char in new_content:
                            if char == '\n':
                                response_lines.append('')
                            else:
                                if response_lines:
                                    response_lines[-1] += char
                                else:
                                    response_lines.append(char)
                        # Update chat_history for display, excluding system messages
                        display_history = [
                            f"> {msg['content']}" if msg['role'] == 'user' else f"API: {msg['content']}"
                            for msg in chat_history if msg['role'] != 'system'
                        ] + [f"API: {''.join(response_lines)}"]
                        line_writer('\n'.join(display_history), scroll_offset=scroll_offset)
        except Exception as e:
            with chat_lock:
                print(e)
                response_lines.append(f"[Error] {str(e)}")
                display_history = [
                    f"> {msg['content']}" if msg['role'] == 'user' else f"ChatGPT: {msg['content']}"
                    for msg in chat_history if msg['role'] != 'system'
                ] + ["API: [Error]"]
                line_writer('\n'.join(display_history), scroll_offset=scroll_offset)

    while True:
        clear_display()
        # Display chat history with current scroll offset, excluding system messages
        with chat_lock:
            display_history = [
                f"> {msg['content']}" if msg['role'] == 'user' else f"API: {msg['content']}"
                for msg in chat_history if msg['role'] != 'system'
            ]
            display_text = "\n".join(display_history)
            line_writer(display_text, scroll_offset)

        # Display user input prompt on the first line
        draw.text((0, 0), f"> {user_input}", font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key in ENTER_KEYS:
            if user_input.strip():
                chat_history.append({"role": "user", "content": user_input.strip()})
                user_input = ""
                # Reset scroll_offset to show the latest messages
                scroll_offset = max(0, len(display_text.split('\n')) - MAX_DISPLAY_LINES)
                # Start streaming response
                is_streaming = True
                stop_stream = False
                stream_thread = threading.Thread(target=stream_response)
                stream_thread.start()
        elif key == ESCAPE:
            stop_stream = True
            if is_streaming:
                stream_thread.join()
            return
        elif key == curses.KEY_UP:
            if scroll_offset > 0:
                scroll_offset -= 1
        elif key == curses.KEY_DOWN:
            # Calculate total lines excluding the user input prompt
            total_lines = len(display_text.split('\n'))
            if scroll_offset < total_lines - MAX_DISPLAY_LINES:
                scroll_offset += 1
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            user_input = user_input[:-1]
            # Optionally adjust scroll_offset if needed
        elif 32 <= key <= 126 and len(user_input) < 100:
            user_input += chr(key)
            # Optionally adjust scroll_offset if needed
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

    while True:
        clear_display()
        draw.text((0, 0), "Select a file:", font=font, fill=WHITE)
        for idx, filename in enumerate(files[:MAX_DISPLAY_LINES]):
            if idx == current_selection:
                line = "> " + filename
            else:
                line = "  " + filename
            draw.text((0, (idx + 1) * (FONT_SIZE + 2)), line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % min(len(files), MAX_DISPLAY_LINES)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % min(len(files), MAX_DISPLAY_LINES)
        elif key in ENTER_KEYS:
            return files[current_selection]
        elif key == ESCAPE:
            return None
        time.sleep(0.05)

def show_help(stdscr):
    """Display the help information with scrollable text."""
    help_text = (
        "Word Processor Help\n"
        "Use arrow keys to navigate menus and scroll help text.\n"
        "Type to enter text into files.\n"
        "Press Enter to confirm actions.\n"
        "Press Esc to save and exit editing."
    )
    lines = help_text.split('\n')
    current_line = 0
    total_lines = len(lines)

    while True:
        clear_display()
        display_lines = lines[current_line:current_line + MAX_DISPLAY_LINES]
        for idx, line in enumerate(display_lines):
            # Handle word wrapping if necessary
            wrapped = wrap_text(line, max_chars=21)
            for w_idx, w_line in enumerate(wrapped):
                if idx + w_idx >= MAX_DISPLAY_LINES:
                    break
                draw.text((0, (idx + w_idx) * (FONT_SIZE + 2)), w_line, font=font, fill=WHITE)
        display_image()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_line > 0:
            current_line -= 1
        elif key == curses.KEY_DOWN and current_line < total_lines - MAX_DISPLAY_LINES:
            current_line += 1
        elif key == ESCAPE:
            return
        time.sleep(0.05)

def wrap_text(text, max_chars):
    """Wrap text to a maximum number of characters per line."""
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            if current_line:
                current_line += ' ' + word
            else:
                current_line = word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines[:MAX_DISPLAY_LINES]  # Limit to max lines

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
