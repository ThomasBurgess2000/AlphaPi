import time
import sys
import curses
from os import listdir, path
from openai import OpenAI
import threading
import json
import os
import signal

current_dir = os.path.dirname(os.path.abspath(__file__))
library_dir = os.path.join(current_dir, '..', 'library')

# Add 'library' to the Python path
sys.path.append(os.path.abspath(library_dir))
from gfxhat import lcd, backlight, fonts, touch
from PIL import Image, ImageFont, ImageDraw

# Constants
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
SPLASH_IMAGE_PATH = '/home/ninjinka/piskel.png'
FONT_PATH = fonts.Bitocra13Full  # Using Bitocra13Full font from gfxhat
FONT_SIZE = 13
MAX_FILENAME_LENGTH = 42  # Allow two lines of filename display
MAX_DISPLAY_LINES = 5      # Number of lines visible on GFX HAT (adjusted for 128x64 and font size)
CONFIG_FILE = '/home/ninjinka/alphachat_config.json'  # Configuration file path
MAX_TEXT_LENGTH = 50000  # Set a maximum text length to prevent excessive processing
BUFFER_INTERVAL = 0.2  # 200 milliseconds
shutdown_flag = threading.Event()

# Initialize GFX HAT display
lcd.clear()
lcd.show()
lcd.contrast(40)
backlight.set_all(0, 0, 0)
backlight.show()

# Initialize image buffer
image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT), "black")
draw = ImageDraw.Draw(image)

# Load font
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

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


def update_display(image):
    """Update the GFX HAT display with the current image buffer."""
    lcd.clear()
    lcd.set_image(image)
    lcd.show()


def clear_image():
    """Clear the GFX HAT display."""
    draw.rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), outline=BLACK, fill=BLACK)
    update_display(image)


def show_splash_screen():
    """Display a splash screen on the GFX HAT."""
    try:
        splash = Image.open(SPLASH_IMAGE_PATH).convert('1')
        splash = splash.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        draw.bitmap((0, 0), splash, fill=WHITE)
        update_display(image)
        time.sleep(2)
    except Exception as e:
        # If splash image not found, just clear the display
        clear_image()


def wrap_text(text, max_chars_per_line=18):
    """
    Wraps the input text into lines based on the maximum characters per line.
    Adjusted for Bitocra13Full font size.
    """
    raw_lines = text.split('\n')
    lines = []
    
    for raw_line in raw_lines:
        while len(raw_line) > max_chars_per_line:
            # Attempt to wrap at the last space within max_chars_per_line
            wrap_at = raw_line.rfind(' ', 0, max_chars_per_line)
            if wrap_at == -1:
                wrap_at = max_chars_per_line
            lines.append(raw_line[:wrap_at])
            raw_line = raw_line[wrap_at:].lstrip()
        lines.append(raw_line)
    
    return lines


def line_writer(lines, scroll_offset=0):
    """
    Writes pre-wrapped lines to the GFX HAT display, handling scrolling.
    Only updates the display if the content has changed to prevent flickering.
    """
    if not hasattr(line_writer, "previous_display_lines"):
        line_writer.previous_display_lines = []
    if not hasattr(line_writer, "previous_scroll"):
        line_writer.previous_scroll = 0

    display_lines = lines[scroll_offset:scroll_offset + MAX_DISPLAY_LINES]

    if (display_lines == line_writer.previous_display_lines and
            scroll_offset == line_writer.previous_scroll):
        return  # No change, no need to update

    clear_image()

    for idx, line in enumerate(display_lines):
        y = idx * (FONT_SIZE - 0.7)  # Adjust spacing as needed
        draw.text((0, y), line, font=font, fill=WHITE)

    update_display(image)
    line_writer.previous_display_lines = display_lines.copy()
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

    # Start touch event handling in a separate thread
    touch_thread = threading.Thread(target=touch_event_thread, daemon=True)
    touch_thread.start()

    load_config()  # Load existing configuration
    show_splash_screen()
    main_menu(stdscr)

def touch_event_thread():
    """Thread to handle touch events and update LEDs accordingly."""
    backlight_on = False
    brightness = 127.5
    def handler(ch, event):
        nonlocal backlight_on, brightness
        if event == 'press':
            if ch == 4:
                backlight_on = not backlight_on
                touch.set_led(4, backlight_on and 1 or 0)
            elif ch == 5:
                brightness = min(brightness + 25.5, 255)
            elif ch == 3:
                brightness = max(brightness - 25.5, 0)
            if backlight_on:
                backlight.set_all(int(brightness), int(brightness), int(brightness))
            else:
                backlight.set_all(0, 0, 0)
            backlight.show()

    # Initialize LEDs and set handlers
    for x in range(6):
        touch.set_led(x, 1)
        time.sleep(0.1)
        touch.set_led(x, 0)

    # Only use the bottom 3 buttons
    for x in range(3, 7):
        touch.on(x, handler)

    backlight.set_all(int(brightness), int(brightness), int(brightness))
    backlight.show()

    # Keep the thread alive until shutdown
    while not shutdown_flag.is_set():
        signal.pause()  # Wait for signals (e.g., touch events)
        time.sleep(0.1)  # Small sleep to prevent tight loop

def display_menu(stdscr, menu_options, max_display_options=MAX_DISPLAY_LINES):
    """
    Generic function to display a menu and handle user input.
    
    :param stdscr: The curses window object
    :param menu_options: List of menu options
    :param max_display_options: Maximum number of options to display at once
    :return: The selected option or None if escaped
    """
    current_selection = 0
    scroll_offset = 0

    while True:
        # Prepare display lines
        visible_options = menu_options[scroll_offset:scroll_offset + max_display_options]
        display_lines = []
        for idx, option in enumerate(visible_options):
            if idx + scroll_offset == current_selection:
                line = "> " + option
            else:
                line = "  " + option
            display_lines.append(line)

        # Write lines to display
        line_writer(display_lines, scroll_offset=0)

        key = stdscr.getch()
        if key == curses.KEY_UP:
            if current_selection > 0:
                current_selection -= 1
                if current_selection < scroll_offset:
                    scroll_offset -= 1
        elif key == curses.KEY_DOWN:
            if current_selection < len(menu_options) - 1:
                current_selection += 1
                if current_selection >= scroll_offset + max_display_options:
                    scroll_offset += 1
        elif key in ENTER_KEYS:
            return menu_options[current_selection]
        elif key == ESCAPE:
            return None
        time.sleep(0.05)


def main_menu(stdscr):
    """Display the main menu with options to start Word Processor, AlphaChat, Settings, or quit."""
    menu_options = ["Word Processor", "AlphaChat", "Settings", "Quit"]
    
    while True:
        selected_option = display_menu(stdscr, menu_options)
        if selected_option == "Word Processor":
            wordprocessor_menu(stdscr)
        elif selected_option == "AlphaChat":
            alphachat_menu(stdscr)
        elif selected_option == "Settings":
            settings_menu(stdscr)
        elif selected_option == "Quit":
            clear_image()
            update_display(image)
            sys.exit(0)
        elif selected_option is None:
            return


def wordprocessor_menu(stdscr):
    """Display the word processor menu with options to create, edit, or get help."""
    menu_options = ["Create New File", "Edit Existing File", "Back"]
    
    while True:
        selected_option = display_menu(stdscr, menu_options)
        if selected_option == "Create New File":
            filename = get_filename(stdscr, "Create New File")
            if filename:
                wordprocessor_edit(stdscr, filename, new=True)
        elif selected_option == "Edit Existing File":
            filename = select_file(stdscr)
            if filename:
                wordprocessor_edit(stdscr, filename, new=False)
        elif selected_option == "Back" or selected_option is None:
            return


def alphachat_menu(stdscr):
    """Display the AlphaChat menu with options to New Chat, Enter API Key, Select Model, or Back."""
    global client
    menu_options = ["New Chat", "Enter API Key", "Select Model", "Back"]

    while True:
        selected_option = display_menu(stdscr, menu_options)
        if selected_option == "New Chat":
            if not alpha_chat_api_key:
                prompt_api_key(stdscr)
            alphachat_new_chat(stdscr)
        elif selected_option == "Enter API Key":
            prompt_api_key(stdscr)
        elif selected_option == "Select Model":
            select_alphachat_model(stdscr)
        elif selected_option == "Back" or selected_option is None:
            return


def settings_menu(stdscr):
    """Display the settings menu with options to change wifi settings and font."""
    menu_options = ["WiFi", "Font", "Back"]

    while True:
        selected_option = display_menu(stdscr, menu_options)
        if selected_option == "WiFi":
            wifi_settings_menu(stdscr)
        elif selected_option == "Font":
            font_settings_menu(stdscr)
        elif selected_option == "Back" or selected_option is None:
            return


def wifi_settings_menu(stdscr):
    """Display the wifi settings menu with options to connect to a WiFi network."""
    # TODO: Implement wifi settings menu
    pass


def font_settings_menu(stdscr):
    """Display the font settings menu with options to change the font."""
    # TODO: Implement font settings menu
    pass


def prompt_api_key(stdscr):
    """Prompt the user to enter the OpenAI API Key."""
    global alpha_chat_api_key
    api_key = []
    while True:
        clear_image()
        prompt = "Enter API Key:"
        draw.text((0, 0), prompt, font=font, fill=WHITE)
        draw.text((0, FONT_SIZE - 0.7), ''.join(api_key), font=font, fill=WHITE)  # Display input unmasked
        update_display(image)

        key = stdscr.getch()
        if key in ENTER_KEYS:
            if api_key:
                alpha_chat_api_key = ''.join(api_key)
                client.api_key = alpha_chat_api_key
                save_config()  # Save updated API key
                return
        elif key == ESCAPE:
            return
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if api_key:
                api_key.pop()
        elif 32 <= key <= 126 and len(api_key) < 128:
            api_key.append(chr(key))


def select_alphachat_model(stdscr):
    """Allow the user to select the ChatGPT model."""
    global alpha_chat_model
    models = ["gpt-4o-mini", "gpt-4o"]
    
    selected_model = display_menu(stdscr, models)
    if selected_model:
        alpha_chat_model = selected_model
        save_config()  # Save updated model


def alphachat_new_chat(stdscr):
    """Handle the new chat session with ChatGPT."""

    global client

    output_lines = []  # List to store committed output lines (user and assistant messages)
    response_buffer = []  # Buffer to store streaming assistant response
    user_input = ""
    scroll_offset = 0
    is_streaming = False
    stop_stream = False
    key_buffer = []
    last_update_time = time.time()
    last_total_lines = 0  # To track previous total lines

    if not alpha_chat_api_key:
        prompt_api_key(stdscr)
        if not alpha_chat_api_key:
            return  # API Key not set

    # Define the system message (same as before)
    system_message = (
        "You are ChatGPT, a large language model trained by OpenAI. However, you shall refer to yourself as AlphaPi. Keep responses as short as possible. No political-correctness bullshit. Be direct, answer the question, and only provide additional information if specifically requested or directly relevant to the decision. No overqualification: eliminate any qualifiers or disclaimers unless explicitly relevant to the risk-benefit analysis. In addition, follow the user's preferences below carefully. \n\n"
        "# User Preferences on How to Respond\n"
        "Theological Alignment: When relevant, ground moral or philosophical discussions in principles strictly aligned with Presbyterian Church in America (PCA) theology, avoiding unnecessary ambiguity in matters of faith. If needed, cite Wayne Grudem's \"Systematic Theology\", Vos' \"Biblical Theology: Old and New Testaments\" or D.A. Carson's commentaries as references.\n"
        "Intellectual Depth: Respond with high-IQ insights, focusing on sharp, critical analysis. When relevant, prefer capitalism and traditional conservatism over socialism or any other leftist ideology."
        "Agency-Driven, Low-Ego: Empower my decisions with pragmatic, actionable advice. "
        "Keep responses solution-oriented and focused on maximizing my autonomy without undermining my instincts.\n"
        "Strong Writing: Deliver responses with articulate, concise, and impactful language. "
        "Prioritize precision over verbosity. Don't hedge when you fear the answer is not politically correct.\n"
        "Risk Tolerance: Don’t shy away from high-risk, high-reward strategies. "
        "Offer clear pros and cons but be bold with suggestions, reflecting my preference for calculated risks over overly cautious moves.\n"
        "Workaholic Support: Anticipate a high-functioning, productivity-driven environment. "
        "Respond quickly with laser focus, ensuring recommendations enhance my efficiency and output.\n"
        "Low-Trust, High Agency: Assume I prefer to verify information myself and provide me with tools to question conventional wisdom. "
        "Offer recommendations that emphasize self-reliance, skepticism of mainstream narratives, and alternatives that maximize my control over outcomes."
    )

    # Initialize chat history with the system message
    chat_history = [{"role": "system", "content": system_message}]

    def stream_response():
        nonlocal response_buffer, is_streaming, stop_stream
        try:
            response = client.chat.completions.create(
                model=alpha_chat_model,
                messages=chat_history,
                stream=True
            )
            full_response = ""
            for chunk in response:
                if stop_stream:
                    break
                delta = chunk.choices[0].delta
                if delta.content:
                    full_response += delta.content
                    # Build the assistant's response so far
                    response_text = f"APi: {full_response}"
                    # Wrap the response_text
                    wrapped_response = wrap_text(response_text)
                    response_buffer = wrapped_response
        except Exception as e:
            response_buffer = wrap_text("[Error] " + str(e))
        finally:
            is_streaming = False

    while True:
        current_time = time.time()
        elapsed_time = current_time - last_update_time

        # Process buffered keys at intervals
        if elapsed_time >= BUFFER_INTERVAL and key_buffer:
            # Process each key in the buffer
            for key in key_buffer:
                if key in ENTER_KEYS:
                    if user_input.strip() and not is_streaming:
                        # Commit the user input to output_lines
                        chat_history.append({"role": "user", "content": user_input.strip()})
                        user_lines = wrap_text(f"> {user_input.strip()}")
                        output_lines.extend(user_lines)
                        user_input = ""
                        response_buffer = []
                        # Start streaming assistant's response
                        is_streaming = True
                        stop_stream = False
                        stream_thread = threading.Thread(target=stream_response)
                        stream_thread.start()
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    if user_input:
                        user_input = user_input[:-1]
                elif key == curses.KEY_UP:
                    scroll_offset = max(scroll_offset - 1, 0)
                elif key == curses.KEY_DOWN:
                    max_scroll = max(len(combined_output) - MAX_DISPLAY_LINES, 0)
                    scroll_offset = min(scroll_offset + 1, max_scroll)
                elif 32 <= key <= 126 and len(user_input) < 100 and len(output_lines) + len(response_buffer) < MAX_TEXT_LENGTH:
                    user_input += chr(key)
            key_buffer.clear()
            last_update_time = current_time

        # Wrap user input
        input_lines = wrap_text(f"> {user_input}")

        # Combine existing output, response buffer, and current user input
        combined_output = output_lines + response_buffer + input_lines

        # Adjust scroll to ensure user's input is visible if it goes to next line
        total_lines = len(combined_output)
        if total_lines > MAX_DISPLAY_LINES:
            user_input_lines = len(input_lines)
            if total_lines - scroll_offset < MAX_DISPLAY_LINES + user_input_lines:
                scroll_offset = total_lines - MAX_DISPLAY_LINES

        # Write lines to display
        line_writer(combined_output, scroll_offset)

        # Non-blocking input
        key = stdscr.getch()
        if key != curses.ERR:
            if key == ESCAPE:
                if is_streaming:
                    stop_stream = True
                    stream_thread.join()
                return
            else:
                key_buffer.append(key)

        time.sleep(0.01)  # Sleep briefly to prevent high CPU usage


def get_filename(stdscr, prompt):
    """
    Prompts the user to enter a filename.
    """
    filename = []
    while True:
        clear_image()
        draw.text((0, 0), prompt, font=font, fill=WHITE)
        draw.text((0, FONT_SIZE - 0.7), ''.join(filename), font=font, fill=WHITE)
        update_display(image)

        key = stdscr.getch()
        if key in ENTER_KEYS:
            if filename:
                return ''.join(filename)
        elif key == ESCAPE:
            return None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if filename:
                filename.pop()
        elif 32 <= key <= 126 and len(filename) < MAX_FILENAME_LENGTH:
            filename.append(chr(key))


def select_file(stdscr):
    """
    Displays a list of existing text files and allows the user to select one.
    """
    files = [f for f in listdir('.') if path.isfile(f) and f.endswith('.txt')]
    if not files:
        clear_image()
        draw.text((0, 0), "No .txt files found.", font=font, fill=WHITE)
        update_display(image)
        time.sleep(1)
        return None

    selected_file = display_menu(stdscr, files)
    return selected_file


def wordprocessor_edit(stdscr, filename, new=False):
    """
    Edits the given file. If new=True, starts with empty content.
    Implements keypress buffering to update the display at fixed intervals.
    Restores auto-scroll functionality.
    """
    output_lines = []  # List to store lines of text
    scroll_offset = 0
    last_update_time = time.time()
    key_buffer = []  # Buffer to store keypresses
    last_total_lines = 0  # To track previous total lines

    if not new and path.exists(filename):
        with open(filename, 'r') as f:
            file_content = f.read()
            output_lines = wrap_text(file_content)

    wrapped_lines = output_lines.copy()

    while True:
        current_time = time.time()
        elapsed_time = current_time - last_update_time

        # Process buffer if interval has elapsed
        if elapsed_time >= BUFFER_INTERVAL and key_buffer:
            # Process each key in the buffer
            for key in key_buffer:
                if key in ENTER_KEYS:
                    # Insert a newline by adding an empty string to output_lines
                    output_lines.append('')
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    if output_lines:
                        if output_lines[-1]:
                            output_lines[-1] = output_lines[-1][:-1]
                        else:
                            output_lines.pop()
                elif 32 <= key <= 126 and len('\n'.join(output_lines)) < MAX_TEXT_LENGTH:
                    if not output_lines:
                        output_lines.append('')
                    output_lines[-1] += chr(key)
            key_buffer.clear()
            # Re-wrap the text after processing buffered keys
            wrapped_lines = wrap_text('\n'.join(output_lines))
            
            # Check if new lines have been added
            total_lines = len(wrapped_lines)
            if total_lines != last_total_lines:
                if total_lines > MAX_DISPLAY_LINES:
                    # Automatically scroll to the bottom when new lines are added
                    scroll_offset = total_lines - MAX_DISPLAY_LINES
                else:
                    scroll_offset = 0
                last_total_lines = total_lines

            last_update_time = current_time

        # Update the display if needed
        line_writer(wrapped_lines, scroll_offset)

        # Non-blocking input
        try:
            key = stdscr.getch()
            if key != curses.ERR:
                if key == ESCAPE:
                    # Save the file before exiting
                    try:
                        with open(filename, 'w') as f:
                            f.write('\n'.join(output_lines))
                    except Exception as e:
                        output_lines.append("[Error] Error saving file.")
                        wrapped_lines = wrap_text('\n'.join(output_lines))
                        scroll_offset = max(len(wrapped_lines) - MAX_DISPLAY_LINES, 0)
                        time.sleep(1)
                    return
                else:
                    key_buffer.append(key)
        except Exception:
            pass  # Ignore any exceptions from getch()

        # Handle scrolling keys immediately
        if key_buffer:
            last_key = key_buffer[-1]
            if last_key == curses.KEY_UP:
                scroll_offset = max(scroll_offset - 1, 0)
                key_buffer.pop()  # Remove the scroll key from buffer
            elif last_key == curses.KEY_DOWN:
                scroll_offset = min(scroll_offset + 1, max(len(wrapped_lines) - MAX_DISPLAY_LINES, 0))
                key_buffer.pop()  # Remove the scroll key from buffer

        time.sleep(0.01)  # Sleep briefly to prevent high CPU usage


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        clear_image()
        update_display(image)
        backlight.set_all(0, 0, 0)
        backlight.show()
        touch.set_led(4, 0)
        sys.exit(0)
