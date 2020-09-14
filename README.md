# oled_bonnet

These are Python scripts that are meant to be used with the Adafruit 2.23" Monochrome OLED Bonnet (https://learn.adafruit.com/adafruit-2-23-monochrome-oled-bonnet/overview).

## game.py
game.py allows you to use pygame functions and event handling without using its display functions (you continue to use PIL for that). The main point is to be able to use pygame for key presses.

## photo.py 
photo.py displays an image that you add to the same directory as the script.

## typer.py
typer.py is currently non-functional. Trying to make a way to display input from keyboard using keyboard polling without pygame, but it's not working yet. Feel free to help on this.
