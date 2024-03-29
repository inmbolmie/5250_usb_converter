# Copyright 2020 Inmbolmie <inmbolmie@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import _thread
import time
import argparse
import array
import code
import errno
import fcntl
import os
import pty
import select
import signal
import socket
import stat
import sys
import termios
import tty
import queue
import string
import random
import cmd

# Some important default parameters

# Configure the defaulf dictionary to use if nothing is specified in the
# command line, from those defined in scancodeDictionaries
DEFAULT_SCANCODE_DICTIONARY = '5250_ES'

# Configure the defaulf station address if nothing is specified in the
# command line
DEFAULT_STATION_ADDRESS = 0

# Configure the defaulf slow polling value to use if nothing is specified in
# the command line
DEFAULT_SLOW_POLLING = 0
SLOW_POLL_MICROSECONDS = 5000
ULTRA_SLOW_POLL_MICROSECONDS = 1000000

# Keyboard clicker enabled or not by default
DEFAULT_KEYBOARD_CLICKER_ENABLED = True

# Default EBCDIC codepage for character translations
DEFAULT_CODEPAGE = 'cp037'

# Default state for advanced features
DEFAULT_FEATURES = False

# Scancode lookup tables
# Format is the scancode as a key and a 4 or 5 sized array:
# SCANCODE: [POS0, POS1, POS2, POS3, POS4]
# Position 0: Normal key
# Position 1: Shift + key
# Position 2: Alt + key
# Position 3: Ctrl + key
# Position 4 (optional): Extra char to send when the first char resolves to
#                        ESC (0x1B)
# Position 5 (optional): When the EXTRA scancode is received before the given
#                        scancode, send 0x1B plus this char

scancodeDictionaries = {

    '5250_ES': {

        # SPECIAL KEYS MAPPINGS
        'CTRL_PRESS': [0x54],
        'CTRL_RELEASE': [0xD4],
        'ALT_PRESS': [0x68],
        'ALT_RELEASE': [],
        'SHIFT_PRESS': [0x57, 0x56],
        'SHIFT_RELEASE': [0xD7, 0xD6],
        'CAPS_LOCK': [0x7E],
        'EXTRA': [],

        # FUNCTION BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x7C: [chr(0x1B), chr(0x1B), '', ''],  # F1 as ESC
        0x6F: [chr(0x1B), chr(0x1B), '', ''],  # F2 as ESC
        # ROW 2
        0x6C: ['', '', '', ''],  # F3
        0x6D: ['', '', '', ''],  # F4
        # ROW 3
        0x6E: ['', '', '', ''],  # F5
        0x7D: ['', '', '', ''],  # F6
        # ROW 4
        0x71: ['', '', '', ''],  # F7
        0x70: ['', '', '', ''],  # F8
        # ROW 5
        0x72: ['', '', '', ''],  # F9
        0x73: ['', '', '', ''],  # F10

        # MAIN ALPHA AND NUMPAD BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x3E: ['º', 'ª', '\\', ''],
        0x31: ['1', '!', '|', ''],
        0x32: ['2', '"', '@', ''],
        0x33: ['3', '·', '#', ''],
        0x34: ['4', '$', '~', ''],
        0x35: ['5', '%', '½', ''],
        0x36: ['6', '&', '', ''],
        0x37: ['7', '/', '', ''],
        0x38: ['8', '(', '', ''],
        0x39: ['9', ')', '', ''],
        0x3A: ['0', '=', '', ''],
        0x3B: ['\'', '?', '', chr(0x1C)],
        0x3C: ['¡', '¿', '', ''],
        0x3D: [chr(0x08), chr(0x08), '', ''],  # BS
        0x4B: ['', '', '', ''],
        0x4C: ['', '', '', ''],  # DUP
        # ROW 2
        0x20: [chr(0x09), chr(0x09), '', ''],  # TAB
        0x21: ['q', 'Q', '', chr(0x11)],
        0x22: ['w', 'W', '', chr(0x17)],
        0x23: ['e', 'E', '', chr(0x05)],
        0x24: ['r', 'R', '', chr(0x12)],
        0x25: ['t', 'T', '', chr(0x14)],
        0x26: ['y', 'Y', '', chr(0x19)],
        0x27: ['u', 'U', '', chr(0x15)],
        0x28: ['i', 'I', '', chr(0x09)],
        0x29: ['o', 'O', '', chr(0x0F)],
        0x2A: ['p', 'P', '', chr(0x10)],
        0x2B: ['`', '^', '[', chr(0x1B)],
        0x2C: ['+', '*', ']', chr(0x1D)],
        0x2D: [chr(0x0D), chr(0x0D), '', ''],  # ENTER
        0x47: ['7', '7', '', ''],
        0x48: ['8', '8', chr(0x1B), chr(0x1B), 'A'],  # NUMPAD 8 and UP ARROW
        0x49: ['9', '9', '', ''],
        0x4E: ['', '', '', ''],  # CAMPO-
        # ROW 3
        # 0x54: ['', '', ''], #SHIFT
        0x11: ['a', 'A', '', chr(0x01)],
        0x12: ['s', 'S', '', chr(0x13)],
        0x13: ['d', 'D', '', chr(0x04)],
        0x14: ['f', 'F', '', chr(0x06)],
        0x15: ['g', 'G', '', chr(0x07)],
        0x16: ['h', 'H', '', chr(0x08)],
        0x17: ['j', 'J', '', chr(0x0A)],
        0x18: ['k', 'K', '', chr(0x0B)],
        0x19: ['l', 'L', '', chr(0x0C)],
        0x1A: ['ñ', 'Ñ', '', ''],
        0x1B: ['´', '¨', '{', chr(0x1B)],
        0x1C: ['ç', 'Ç', '}', chr(0x1D)],
        0x44: ['4', '4', chr(0x1B), chr(0x1B), 'D'],  # NUMPAD 4 and LEFT ARROW
        0x45: ['5', '5', '', ''],
        # NUMPAD 6 and RIGHT ARROW
        0x46: ['6', '6', chr(0x1B), chr(0x1B), 'C'],
        0x4D: [chr(0x0D), '', '', ''],  # ENTER
        # ROW 4
        # 0x57: ['', '', ''], #CTRL
        0x0E: ['<', '>', '|', ''],
        0x01: ['z', 'Z', '', chr(0x1A)],
        0x02: ['x', 'X', '', chr(0x18)],
        0x03: ['c', 'C', '', chr(0x03)],
        0x04: ['v', 'V', '', chr(0x16)],
        0x05: ['b', 'B', '', chr(0x02)],
        0x06: ['n', 'N', '', chr(0x0E)],
        0x07: ['m', 'M', '', chr(0x0D)],
        0x08: [',', ';', '', ''],
        0x09: ['.', ':', '', ''],
        0x0A: ['-', '_', '', chr(0x1F)],
        # 0x56: ['', '', ''], #ALT
        0x0C: ['', '', '', ''],
        0x41: ['1', '1', '', ''],
        0x42: ['2', '2', chr(0x1B), chr(0x1B), 'B'],  # NUMPAD 2 and DOWN ARROW
        0x43: ['3', '3', '', ''],
        0x68: ['', '', '', ''],
        0x40: ['0', '0', '', ''],
        0x4A: [',', '', '', ''],
        # ROW 5
        0x0F: [' ', ' ', '', ''],  # SPACE BAR

        # Custom character conversions, from ASCII char to EBCDIC code that
        # will override the DEFAULT_CODEPAGE conversions
        'CUSTOM_CHARACTER_CONVERSIONS': {
            '[': 0x4A,
            ']': 0x5A,
            '^': 0x95,
            '#': 0xBC
        },
    },

    '5250_US': {

        # SPECIAL KEYS MAPPINGS
        'CTRL_PRESS': [0x54],
        'CTRL_RELEASE': [0xD4],
        'ALT_PRESS': [0x68],
        'ALT_RELEASE': [],
        'SHIFT_PRESS': [0x57, 0x56],
        'SHIFT_RELEASE': [0xD7, 0xD6],
        'CAPS_LOCK': [0x7E],
        'EXTRA': [],

        # FUNCTION BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x7C: [chr(0x1B), chr(0x1B), '', ''],  # F1 as ESC
        0x6F: [chr(0x1B), chr(0x1B), '', ''],  # F2 as ESC
        # ROW 2
        # 0x6C: ['', '', '', ''], #F3
        # 0x6D: ['', '', '', ''], #F4
        # ROW 3
        # 0x6E: ['', '', '', ''], #F5
        # 0x7D: ['', '', '', ''], #F6
        # ROW 4
        # 0x71: ['', '', '', ''], #F7
        # 0x70: ['', '', '', ''], #F8
        # ROW 5
        # 0x72: ['', '', '', ''], #F9
        # 0x73: ['', '', '', ''], #F10

        # MAIN ALPHA AND NUMPAD BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x3E: ['`', '~', '`', ''],
        0x31: ['1', '|', '', ''],
        0x32: ['2', '@', '', ''],
        0x33: ['3', '#', '', ''],
        0x34: ['4', '$', '', ''],
        0x35: ['5', '%', '', ''],
        0x36: ['6', '^', '', ''],
        0x37: ['7', '&', '', ''],
        0x38: ['8', '*', '', ''],
        0x39: ['9', '(', '', ''],
        0x3A: ['0', ')', '', ''],
        0x3B: ['-', '_', '', chr(0x1C)],
        0x3C: ['=', '+', '', ''],
        0x3D: [chr(0x08), chr(0x08), '', ''],  # BS
        0x4B: ['', '', '', ''],
        0x4C: ['', '', '', ''],  # DUP
        # ROW 2
        0x20: [chr(0x09), chr(0x09), '', ''],  # TAB
        0x21: ['q', 'Q', '', chr(0x11)],
        0x22: ['w', 'W', '', chr(0x17)],
        0x23: ['e', 'E', '', chr(0x05)],
        0x24: ['r', 'R', '', chr(0x12)],
        0x25: ['t', 'T', '', chr(0x14)],
        0x26: ['y', 'Y', '', chr(0x19)],
        0x27: ['u', 'U', '', chr(0x15)],
        0x28: ['i', 'I', '', chr(0x09)],
        0x29: ['o', 'O', '', chr(0x0F)],
        0x2A: ['p', 'P', '', chr(0x10)],
        0x2B: ['¢', '!', '', chr(0x1B)],
        0x2C: ['\\', '|', '', chr(0x1D)],
        0x2D: [chr(0x0D), chr(0x0D), '', ''],  # ENTER
        0x47: ['7', '7', '', ''],
        0x48: ['8', '8', chr(0x1B), chr(0x1B), 'A'],  # NUMPAD 8 and UP ARROW
        0x49: ['9', '9', '', ''],
        0x4E: ['', '', '', ''],  # CAMPO-
        # ROW 3
        # 0x54 ['', '', ''], #SHIFT
        0x11: ['a', 'A', '', chr(0x01)],
        0x12: ['s', 'S', '', chr(0x13)],
        0x13: ['d', 'D', '', chr(0x04)],
        0x14: ['f', 'F', '', chr(0x06)],
        0x15: ['g', 'G', '', chr(0x07)],
        0x16: ['h', 'H', '', chr(0x08)],
        0x17: ['j', 'J', '', chr(0x0A)],
        0x18: ['k', 'K', '', chr(0x0B)],
        0x19: ['l', 'L', '', chr(0x0C)],
        0x1A: [';', ':', '', ''],
        0x1B: ['\'', '""', '', chr(0x1B)],
        0x1C: ['{', '}', '', chr(0x1D)],
        0x44: ['4', '4', chr(0x1B), chr(0x1B), 'D'],  # NUMPAD 4 and LEFT ARROW
        0x45: ['5', '5', '', ''],
        # NUMPAD 6 and RIGHT ARROW
        0x46: ['6', '6', chr(0x1B), chr(0x1B), 'C'],
        0x4D: [chr(0x0D), '', '', ''],  # ENTER
        # ROW 4
        # 0x57: ['', '', ''], #CTRL
        0x0E: ['<', '>', '|', ''],
        0x01: ['z', 'Z', '', chr(0x1A)],
        0x02: ['x', 'X', '', chr(0x18)],
        0x03: ['c', 'C', '', chr(0x03)],
        0x04: ['v', 'V', '', chr(0x16)],
        0x05: ['b', 'B', '', chr(0x02)],
        0x06: ['n', 'N', '', chr(0x0E)],
        0x07: ['m', 'M', '', chr(0x0D)],
        0x08: [',', '<', '', ''],
        0x09: ['.', '>', '', ''],
        0x0A: ['/', '?', '', chr(0x1F)],
        # 0x56: ['', '', ''], #ALT
        0x0C: ['', '', '', ''],
        0x41: ['1', '1', '', ''],
        0x42: ['2', '2', chr(0x1B), chr(0x1B), 'B'],  # NUMPAD 2 and DOWN ARROW
        0x43: ['3', '3', '', ''],
        0x68: ['', '', '', ''],
        0x40: ['0', '0', '', ''],
        0x4A: [',', '', '', ''],
        # ROW 5
        0x0F: [' ', ' ', '', ''],  # SPACE BAR

        # Custom character conversions, from ASCII char to EBCDIC code that
        # will override the DEFAULT_CODEPAGE conversions
        'CUSTOM_CHARACTER_CONVERSIONS': {
        },
    },

    '5250_DE': {

        # SPECIAL KEYS MAPPINGS
        'CTRL_PRESS': [0x54],
        'CTRL_RELEASE': [0xD4],
        'ALT_PRESS': [0x68],
        'ALT_RELEASE': [],
        'SHIFT_PRESS': [0x57, 0x56],
        'SHIFT_RELEASE': [0xD7, 0xD6],
        'CAPS_LOCK': [0x7E],
        'EXTRA': [],

        # FUNCTION BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x7C: [chr(0x1B), chr(0x1B), '', ''],  # F1 as ESC
        0x6F: [chr(0x1B), chr(0x1B), '', ''],  # F2 as ESC
        # ROW 2
        # 0x6C: ['', '', '', ''], #F3
        # 0x6D: ['', '', '', ''], #F4
        # ROW 3
        # 0x6E: ['', '', '', ''], #F5
        # 0x7D: ['', '', '', ''], #F6
        # ROW 4
        # 0x71: ['', '', '', ''], #F7
        # 0x70: ['', '', '', ''], #F8
        # ROW 5
        # 0x72: ['', '', '', ''], #F9
        # 0x73: ['', '', '', ''], #F10

        # MAIN ALPHA AND NUMPAD BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x3E: ['^', '°', '′', ''],
        0x31: ['1', '!', '¹', ''],
        0x32: ['2', '"', '²', ''],
        0x33: ['3', '§', '³', ''],
        0x34: ['4', '$', '¼', ''],
        0x35: ['5', '%', '½', ''],
        0x36: ['6', '&', '¬', ''],
        0x37: ['7', '/', '{', ''],
        0x38: ['8', '(', '[', ''],
        0x39: ['9', ')', ']', ''],
        0x3A: ['0', '=', '}', ''],
        0x3B: ['ß', '?', '\\', chr(0x1C)],
        0x3C: ['´', '`', '¸', ''],
        0x3D: [chr(0x08), chr(0x08), '', ''],  # BS
        0x4B: ['', '', '', ''],
        0x4C: ['', '', '', ''],  # DUP
        # ROW 2
        0x20: [chr(0x09), chr(0x09), '', ''],  # TAB
        0x21: ['q', 'Q', '@', chr(0x11)],
        0x22: ['w', 'W', 'ł', chr(0x17)],
        0x23: ['e', 'E', '€', chr(0x05)],
        0x24: ['r', 'R', '¶', chr(0x12)],
        0x25: ['t', 'T', 'ŧ', chr(0x14)],
        0x26: ['z', 'Z', '←', chr(0x19)],
        0x27: ['u', 'U', '↓', chr(0x15)],
        0x28: ['i', 'I', '→', chr(0x09)],
        0x29: ['o', 'O', 'ø', chr(0x0F)],
        0x2A: ['p', 'P', 'þ', chr(0x10)],
        0x2B: ['ü', 'Ü', '¨', chr(0x1B)],
        0x2C: ['+', '*', '~', chr(0x1D)],
        0x2D: [chr(0x0D), chr(0x0D), '', ''],  # ENTER
        0x47: ['7', '7', '', ''],
        0x48: ['8', '8', chr(0x1B), chr(0x1B), 'A'],  # NUMPAD 8 and UP ARROW
        0x49: ['9', '9', '', ''],
        0x4E: ['', '', '', ''],  # CAMPO-
        # ROW 3
        # 0x54: ['', '', ''], #SHIFT
        0x11: ['a', 'A', 'æ', chr(0x01)],
        0x12: ['s', 'S', 'ſ', chr(0x13)],
        0x13: ['d', 'D', 'ð', chr(0x04)],
        0x14: ['f', 'F', 'đ', chr(0x06)],
        0x15: ['g', 'G', 'ŋ', chr(0x07)],
        0x16: ['h', 'H', 'ħ', chr(0x08)],
        0x17: ['j', 'J', '.', chr(0x0A)],
        0x18: ['k', 'K', 'ĸ', chr(0x0B)],
        0x19: ['l', 'L', 'ł', chr(0x0C)],
        0x1A: ['ö', 'Ö', '˝', ''],
        0x1B: ['ä', 'Ä', '^', chr(0x1B)],
        0x1C: ['#', 'Ä', '’', chr(0x1D)],
        0x44: ['4', '4', chr(0x1B), chr(0x1B), 'D'],  # NUMPAD 4 and LEFT ARROW
        0x45: ['5', '5', '', ''],
        # NUMPAD 6 and RIGHT ARROW
        0x46: ['6', '6', chr(0x1B), chr(0x1B), 'C'],
        0x4D: [chr(0x0D), '', '', ''],  # ENTER
        # ROW 4
        # 0x57: ['', '', ''], #CTRL
        0x0E: ['<', '>', '|', ''],
        0x01: ['y', 'Y', '»', chr(0x1A)],
        0x02: ['x', 'X', '«', chr(0x18)],
        0x03: ['c', 'C', '¢', chr(0x03)],
        0x04: ['v', 'V', '„', chr(0x16)],
        0x05: ['b', 'B', '“”', chr(0x02)],
        0x06: ['n', 'N', '”', chr(0x0E)],
        0x07: ['m', 'M', 'µ', chr(0x0D)],
        0x08: [',', ';', '·', ''],
        0x09: ['.', ':', '…', ''],
        0x0A: ['-', '_', '–', chr(0x1F)],
        # 0x56: ['', '', ''], #ALT
        0x0C: ['', '', '', ''],
        0x41: ['1', '1', '', ''],
        0x42: ['2', '2', chr(0x1B), chr(0x1B), 'B'],  # NUMPAD 2 and DOWN ARROW
        0x43: ['3', '3', '', ''],
        0x68: ['', '', '', ''],
        0x40: ['0', '0', '', ''],
        0x4A: [',', '', '', ''],
        # ROW 5
        0x0F: [' ', ' ', '', ''],  # SPACE BAR

        # Custom character conversions, from ASCII char to EBCDIC code that
        # will override the DEFAULT_CODEPAGE conversions
        'CUSTOM_CHARACTER_CONVERSIONS': {
        },
    },

    'ENHANCED_ES': {

        # SPECIAL FUNCTION KEYS MAPPINGS
        'CTRL_PRESS': [0x14],
        'CTRL_RELEASE': [0x94],
        'ALT_PRESS': [0x58],
        'ALT_RELEASE': [],
        'SHIFT_PRESS': [0x12, 0x59],
        'SHIFT_RELEASE': [0x92, 0xD9],
        'CAPS_LOCK': [0x11],
        'EXTRA': [],

        # ESC AND FUNCTION BLOCK KEYS MAPPINGS
        # KEYS FROM LEFT TO RIGHT
        0x08: [chr(0x1B), chr(0x1B), '', ''],  # ESC
        # 0x07: ['', '', '', ''], #F1
        # 0x0F: ['', '', '', ''], #F2
        # 0x17: ['', '', '', ''], #F3
        # 0x1F: ['', '', '', ''], #F4
        # 0x27: ['', '', '', ''], #F5
        # 0x2F: ['', '', '', ''], #F6
        # 0x37: ['', '', '', ''], #F7
        # 0x3F: ['', '', '', ''], #F8
        # 0x47: ['', '', '', ''], #F9
        # 0x4F: ['', '', '', ''], #F10
        # 0x4F: ['', '', '', ''], #F11
        # 0x5E: ['', '', '', ''], #F12

        # MAIN ALPHA BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x0E: ['º', 'ª', '\\', ''],
        0x16: ['1', '!', '|', ''],
        0x1E: ['2', '"', '@', ''],
        0x26: ['3', '·', '#', ''],
        0x25: ['4', '$', '~', ''],
        0x2E: ['5', '%', '½', ''],
        0x36: ['6', '&', '', ''],
        0x3D: ['7', '/', '', ''],
        0x3E: ['8', '(', '', ''],
        0x46: ['9', ')', '', ''],
        0x45: ['0', '=', '', ''],
        0x4E: ['\'', '?', '', chr(0x1C)],
        0x55: ['¡', '¿', '', ''],
        0x66: [chr(0x08), chr(0x08), '', ''],  # BS
        # ROW 2
        0x0D: [chr(0x09), chr(0x09), '', ''],  # TAB
        0x15: ['q', 'Q', '', chr(0x11)],
        0x1D: ['w', 'W', '', chr(0x17)],
        0x24: ['e', 'E', '', chr(0x05)],
        0x2D: ['r', 'R', '', chr(0x12)],
        0x2C: ['t', 'T', '', chr(0x14)],
        0x35: ['y', 'Y', '', chr(0x19)],
        0x3C: ['u', 'U', '', chr(0x15)],
        0x43: ['i', 'I', '', chr(0x09)],
        0x44: ['o', 'O', '', chr(0x0F)],
        0x4D: ['p', 'P', '', chr(0x10)],
        0x5B: ['+', '*', ']', chr(0x1D)],
        0x5A: [chr(0x0D), chr(0x0D), '', ''],  # ENTER
        # ROW 3
        0x1C: ['a', 'A', '', chr(0x01)],
        0x1B: ['s', 'S', '', chr(0x13)],
        0x23: ['d', 'D', '', chr(0x04)],
        0x2B: ['f', 'F', '', chr(0x06)],
        0x34: ['g', 'G', '', chr(0x07)],
        0x33: ['h', 'H', '', chr(0x08)],
        0x3B: ['j', 'J', '', chr(0x0A)],
        0x42: ['k', 'K', '', chr(0x0B)],
        0x4B: ['l', 'L', '', chr(0x0C)],
        0x4C: ['ñ', 'Ñ', '', ''],
        0x52: ['´', '¨', '{', chr(0x1B)],
        0x5C: ['ç', 'Ç', '}', chr(0x1D)],
        # ROW 4
        0x13: ['<', '>', '|', ''],
        0x1A: ['z', 'Z', '', chr(0x1A)],
        0x22: ['x', 'X', '', chr(0x18)],
        0x21: ['c', 'C', '', chr(0x03)],
        0x2A: ['v', 'V', '', chr(0x16)],
        0x32: ['b', 'B', '', chr(0x02)],
        0x31: ['n', 'N', '', chr(0x0E)],
        0x3A: ['m', 'M', '', chr(0x0D)],
        0x41: [',', ';', '', ''],
        0x49: ['.', ':', '', ''],
        0x4A: ['-', '_', '', chr(0x1F)],
        # ROW 5
        0x29: [' ', ' ', '', ''],  # SPACE BAR

        # TEXT EDIT MODE KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # TBD

        # ARROW KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        0x63: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'A'],  # UP ARROW
        0x61: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'D'],  # LEFT ARROW
        0x60: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'B'],  # DOWN ARROW
        0x6A: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'C'],  # RIGHT ARROW

        # NUMPAD KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x4A: ['/', '/', '', ''],
        0x3E: ['*', '*', '', ''],
        0x7F: ['-', '-', '', ''],
        # ROW 2
        0x6C: ['7', '7', '', ''],
        # NUMPAD 8  EXTRA UP ARROW
        0x75: ['8', '8', chr(0x1B), chr(0x1B), 'A'],
        0x7D: ['9', '9', '', ''],
        0x7B: ['+', '+', '', ''],
        # ROW 3
        # NUMPAD 4   EXTRA LEFT ARROW
        0x6b: ['4', '4', chr(0x1B), chr(0x1B), 'D'],
        0x73: ['5', '5', '', ''],
        # NUMPAD 6 EXTRA RIGHT ARROW
        0x74: ['6', '6', chr(0x1B), chr(0x1B), 'C'],
        0x58: [chr(0x0D), '', '', ''],  # ENTER,
        # ROW 4
        0x69: ['1', '1', '', ''],
        # NUMPAD 2  EXTRA DOWN ARROW
        0x72: ['2', '2', chr(0x1B), chr(0x1B), 'B'],
        0x7A: ['3', '3', '', ''],
        # ROW 5
        0x70: ['0', '0', '', ''],
        0x71: ['.', '', '', ''],

        # Custom character conversions, from ASCII char to EBCDIC code that
        # will override the DEFAULT_CODEPAGE conversions
        'CUSTOM_CHARACTER_CONVERSIONS': {
        },
    },

    'ENHANCED_DE': {

        # ESC AND FUNCTION BLOCK KEYS MAPPINGS
        # KEYS FROM LEFT TO RIGHT
        'CTRL_PRESS': [0x14],
        'CTRL_RELEASE': [0x94],
        'ALT_PRESS': [0X58],
        'ALT_RELEASE': [],
        'SHIFT_PRESS': [0x12, 0x59],
        'SHIFT_RELEASE': [0x92, 0xD9],
        'CAPS_LOCK': [0x11],
        'EXTRA': [],
        0x08: [chr(0x1B), chr(0x1B), '', ''],  # ESC
        # 0x07: ['', '', '', ''], #F1
        # 0x0F: ['', '', '', ''], #F2
        # 0x17: ['', '', '', ''], #F3
        # 0x1F: ['', '', '', ''], #F4
        # 0x27: ['', '', '', ''], #F5
        # 0x2F: ['', '', '', ''], #F6
        # 0x37: ['', '', '', ''], #F7
        # 0x3F: ['', '', '', ''], #F8
        # 0x47: ['', '', '', ''], #F9
        # 0x4F: ['', '', '', ''], #F10
        # 0x4F: ['', '', '', ''], #F11
        # 0x5E: ['', '', '', ''], #F12
        # TBD UP TO F24


        # MAIN ALPHA BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x0E: ['^', '°', '′', ''],
        0x16: ['1', '!', '¹', ''],
        0x1E: ['2', '"', '²', ''],
        0x26: ['3', '§', '³', ''],
        0x25: ['4', '$', '¼', ''],
        0x2E: ['5', '%', '½', ''],
        0x36: ['6', '&', '¬', ''],
        0x3D: ['7', '/', '{', ''],
        0x3E: ['8', '(', '[', ''],
        0x46: ['9', ')', ']', ''],
        0x45: ['0', '=', '}', ''],
        0x4E: ['ß', '?', '\\', chr(0x1C)],
        0x55: ['´', '`', '¸', ''],
        0x66: [chr(0x08), chr(0x08), '', ''],  # BS
        # ROW 2
        0x0D: [chr(0x09), chr(0x09), '', ''],  # TAB
        0x15: ['q', 'Q', '@', chr(0x11)],
        0x1D: ['w', 'W', 'ł', chr(0x17)],
        0x24: ['e', 'E', '€', chr(0x05)],
        0x2D: ['r', 'R', '¶', chr(0x12)],
        0x2C: ['t', 'T', 'ŧ', chr(0x14)],
        0x35: ['z', 'Z', '←', chr(0x19)],
        0x3C: ['u', 'U', '↓', chr(0x15)],
        0x43: ['i', 'I', '→', chr(0x09)],
        0x44: ['o', 'O', 'ø', chr(0x0F)],
        0x4D: ['p', 'P', 'þ', chr(0x10)],
        0x5B: ['ü', 'Ü', '~', chr(0x1D)],
        0x5A: [chr(0x0D), chr(0x0D), '', ''],  # ENTER
        # ROW 3
        0x1C: ['a', 'A', 'æ', chr(0x01)],
        0x1B: ['s', 'S', 'ſ', chr(0x13)],
        0x23: ['d', 'D', 'ð', chr(0x04)],
        0x2B: ['f', 'F', 'đ', chr(0x06)],
        0x34: ['g', 'G', 'ŋ', chr(0x07)],
        0x33: ['h', 'H', 'ħ', chr(0x08)],
        0x3B: ['j', 'J', '.', chr(0x0A)],
        0x42: ['k', 'K', 'ĸ', chr(0x0B)],
        0x4B: ['l', 'L', 'ł', chr(0x0C)],
        0x4C: ['ö', 'Ö', '˝', ''],
        0x52: ['ä', 'Ä', '^', chr(0x1B)],
        0x5C: ['#', '\'', '’', chr(0x1D)],
        # ROW 4
        0x13: ['<', '>', '|', ''],
        0x1A: ['y', 'Y', '»', chr(0x1A)],
        0x22: ['x', 'X', '«', chr(0x18)],
        0x21: ['c', 'C', '¢', chr(0x03)],
        0x2A: ['v', 'V', '„', chr(0x16)],
        0x32: ['b', 'B', '“”', chr(0x02)],
        0x31: ['n', 'N', '”', chr(0x0E)],
        0x3A: ['m', 'M', 'µ', chr(0x0D)],
        0x41: [',', ';', '·', ''],
        0x49: ['.', ':', '…', ''],
        0x4A: ['-', '_', '–', chr(0x1F)],
        # ROW 5
        0x29: [' ', ' ', '', ''],  # SPACE BAR
        0x2B: ['`', '^', '¨', chr(0x1B)],

        # TEXT EDIT MODE KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # TBD

        # ARROW KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        0x63: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'A'],  # UP ARROW
        0x61: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'D'],  # LEFT ARROW
        0x60: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'B'],  # DOWN ARROW
        0x6A: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'C'],  # RIGHT ARROW

        # NUMPAD KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x4A: ['/', '/', '', ''],
        0x3E: ['*', '*', '', ''],
        0x7F: ['-', '-', '', ''],
        # ROW 2
        0x6C: ['7', '7', '', ''],
        # NUMPAD 8  EXTRA UP ARROW
        0x75: ['8', '8', chr(0x1B), chr(0x1B), 'A'],
        0x7D: ['9', '9', '', ''],
        0x7B: ['+', '+', '', ''],
        # ROW 3
        # NUMPAD 4   EXTRA LEFT ARROW
        0x6b: ['4', '4', chr(0x1B), chr(0x1B), 'D'],
        0x73: ['5', '5', '', ''],
        # NUMPAD 6 EXTRA RIGHT ARROW
        0x74: ['6', '6', chr(0x1B), chr(0x1B), 'C'],
        0x58: [chr(0x0D), '', '', ''],  # ENTER,
        # ROW 4
        0x69: ['1', '1', '', ''],
        # NUMPAD 2  EXTRA DOWN ARROW
        0x72: ['2', '2', chr(0x1B), chr(0x1B), 'B'],
        0x7A: ['3', '3', '', ''],
        # ROW 5
        0x70: ['0', '0', '', ''],
        0x71: ['.', '', '', ''],

        # Custom character conversions, from ASCII char to EBCDIC code that
        # will override the DEFAULT_CODEPAGE conversions
        'CUSTOM_CHARACTER_CONVERSIONS': {
        },
    },

    '122KEY_DE': {

        # SPECIAL FUNCTION KEYS MAPPINGS
        'CTRL_PRESS': [0x54],
        'CTRL_RELEASE': [0xD4],
        'ALT_PRESS': [0x68],
        'ALT_RELEASE': [],
        'SHIFT_PRESS': [0x57, 0x56],
        'SHIFT_RELEASE': [0xD7, 0xD6],
        'CAPS_LOCK': [0x7E],  # Grdst
        'EXTRA': [0x6F],

        # LEFT FUNCTION KEYS MAPPINGS (F1-F10)
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x7C: [chr(0x1B), chr(0x1B), '', ''],  # ESC
        # TBD UP TO F10

        # TOP FUNCTION KEYS MAPPINGS (F1-F24)
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        # 0x31: ['', '', '', ''], #F1
        # 0x32: ['', '', '', ''], #F2
        # 0x33: ['', '', '', ''], #F3
        # 0x34: ['', '', '', ''], #F4
        # 0x35: ['', '', '', ''], #F5
        # 0x36: ['', '', '', ''], #F6
        # 0x37: ['', '', '', ''], #F7
        # 0x38: ['', '', '', ''], #F8
        # 0x38: ['', '', '', ''], #F9
        # 0x3A: ['', '', '', ''], #F10
        # 0x3B: ['', '', '', ''], #F11
        # 0x3C: ['', '', '', ''], #F12
        # TBD UP TO F24

        # MAIN ALPHA BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x3E: ['^', '°', '′', ''],
        0x31: ['1', '!', '¹', ''],
        0x32: ['2', '"', '²', ''],
        0x33: ['3', '§', '³', ''],
        0x34: ['4', '$', '¼', ''],
        0x35: ['5', '%', '½', ''],
        0x36: ['6', '&', '¬', ''],
        0x37: ['7', '/', '{', ''],
        0x38: ['8', '(', '[', ''],
        0x39: ['9', ')', ']', ''],
        0x3A: ['0', '=', '}', ''],
        0x3B: ['ß', '?', '\\', chr(0x1C)],
        0x3C: ['´', '`', '¸', ''],
        0x3D: [chr(0x08), chr(0x08), '', ''],  # BS
        # ROW 2
        0x20: [chr(0x09), chr(0x09), '', ''],  # TAB
        0x21: ['q', 'Q', '@', chr(0x11)],
        0x22: ['w', 'W', 'ł', chr(0x17)],
        0x23: ['e', 'E', '€', chr(0x05)],
        0x24: ['r', 'R', '¶', chr(0x12)],
        0x25: ['t', 'T', 'ŧ', chr(0x14)],
        0x26: ['z', 'Z', '←', chr(0x19)],
        0x27: ['u', 'U', '↓', chr(0x15)],
        0x28: ['i', 'I', '→', chr(0x09)],
        0x29: ['o', 'O', 'ø', chr(0x0F)],
        0x2A: ['p', 'P', 'þ', chr(0x10)],
        0x2B: ['ü', 'Ü', '~', chr(0x1D)],
        0x2C: ['+', '*', '~', chr(0x1D)],
        0x2D: [chr(0x0D), chr(0x0D), '', ''],  # ENTER
        # ROW 3
        0x11: ['a', 'A', 'æ', chr(0x01)],
        0x12: ['s', 'S', 'ſ', chr(0x13)],
        0x13: ['d', 'D', 'ð', chr(0x04)],
        0x14: ['f', 'F', 'đ', chr(0x06)],
        0x15: ['g', 'G', 'ŋ', chr(0x07)],
        0x16: ['h', 'H', 'ħ', chr(0x08)],
        0x17: ['j', 'J', '.', chr(0x0A)],
        0x18: ['k', 'K', 'ĸ', chr(0x0B)],
        0x19: ['l', 'L', 'ł', chr(0x0C)],
        0x1A: ['ö', 'Ö', '˝', ''],
        0x1B: ['ä', 'Ä', '^', chr(0x1B)],
        0x1C: ['#', '\'', '’', chr(0x1D)],
        # ROW 4
        0x0e: ['<', '>', '|', ''],
        0x01: ['y', 'Y', '»', chr(0x1A)],
        0x02: ['x', 'X', '«', chr(0x18)],
        0x03: ['c', 'C', '¢', chr(0x03)],
        0x04: ['v', 'V', '„', chr(0x16)],
        0x05: ['b', 'B', '“”', chr(0x02)],
        0x06: ['n', 'N', '”', chr(0x0E)],
        0x07: ['m', 'M', 'µ', chr(0x0D)],
        0x08: [',', ';', '·', ''],
        0x09: ['.', ':', '…', ''],
        0x0a: ['-', '_', '–', chr(0x1F)],
        # ROW 5
        0x0F: [' ', ' ', '', ''],  # SPACE BAR


        # TEXT EDIT MODE KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # TBD

        # ARROW KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        0x71: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'A'],  # UP ARROW
        0x72: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'D'],  # LEFT ARROW
        # TBD CENTER ARROW
        0x73: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'C'],  # RIGHT ARROW
        0x70: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'B'],  # DOWN ARROW

        # NUMPAD KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x4A: ['/', '/', '', ''],
        0x3E: ['*', '*', '', ''],
        0x7F: ['-', '-', '', ''],
        # ROW 2
        0x47: ['7', '7', '', ''],
        # NUMPAD 8  EXTRA UP ARROW
        0x48: ['8', '8', chr(0x1B), chr(0x1B), 'A'],
        0x49: ['9', '9', '', ''],
        0x7B: ['+', '+', '', ''],
        # ROW 3
        # NUMPAD 4   EXTRA LEFT ARROW
        0x44: ['4', '4', chr(0x1B), chr(0x1B), 'D'],
        0x45: ['5', '5', '', ''],
        0x46: ['6', '6', '', '', 'C'],  # NUMPAD 6 EXTRA RIGHT ARROW
        # ROW 4
        0x41: ['1', '1', '', ''],
        # NUMPAD 2  EXTRA DOWN ARROW
        0x42: ['2', chr(0x1B), chr(0x1B), '', 'B'],
        0x43: ['3', '3', '', ''],
        0x2D: [chr(0x0D), '', '', ''],  # ENTER
        # ROW 5
        0x40: ['0', '0', '', ''],
        0x4A: ['.', '', '', ''],

        # Custom character conversions, from ASCII char to EBCDIC code that
        # will override the DEFAULT_CODEPAGE conversions
        'CUSTOM_CHARACTER_CONVERSIONS': {
        },
    },

    '122KEY_EN': {

        # SPECIAL FUNCTION KEYS MAPPINGS
        'CTRL_PRESS': [0x54],
        'CTRL_RELEASE': [0xD4],
        'ALT_PRESS': [0x68],
        'ALT_RELEASE': [],
        'SHIFT_PRESS': [0x57, 0x56],
        'SHIFT_RELEASE': [0xD7, 0xD6],
        'CAPS_LOCK': [0x7E],  # Reset
        'EXTRA': [0x6F],

        # LEFT FUNCTION KEYS MAPPINGS (F1-F10)
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x7C: [chr(0x1B), chr(0x1B), '', ''],  # ESC
        # TBD UP TO F10

        # MAIN ALPHA BLOCK KEYS MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1
        0x3E: ['`', '~', '′', ''],
        # F1 through F12 generate the following scan codes with an
        # 0x6F prefix, so position 5 (EXTRA) is used for those keys.
        # The escape sequences in position 5 correspond to the "xterm"
        # terminfo entry's key_f1 through key_f12.  F13 through F24
        # generate the same scan codes but with a shift key down/make
        # scan code prefix; there is no way to specify handling of the
        # combination of Shift + EXTRA.
        0x31: ['1', '!', '¹', '',         None, 'OP'],
        0x32: ['2', '@', '²', '',         None, 'OQ'],
        0x33: ['3', '#', '³', '',         None, 'OR'],
        0x34: ['4', '$', '¼', '',         None, 'OS'],
        0x35: ['5', '%', '½', '',         None, '[15~'],
        0x36: ['6', '^', '¬', chr(0x1E),  None, '[17~'],
        0x37: ['7', '&', '{', '',         None, '[18~'],
        0x38: ['8', '*', '[', '',         None, '[19~'],
        0x39: ['9', '(', ']', '',         None, '[20~'],
        0x3A: ['0', ')', '}', '',         None, '[21~'],
        0x3B: ['-', '_', '\\', chr(0x1F), None, '[23~'],
        0x3C: ['=', '+', '¸', '',         None, '[24~'],
        0x3D: [chr(0x08), chr(0x08), '', ''],  # BS
        # ROW 2
        0x20: [chr(0x09), chr(0x09), '', ''],  # TAB
        0x21: ['q', 'Q', '@', chr(0x11), None, 'q'],
        0x22: ['w', 'W', 'ł', chr(0x17), None, 'w'],
        0x23: ['e', 'E', '€', chr(0x05), None, 'e'],
        0x24: ['r', 'R', '¶', chr(0x12), None, 'r'],
        0x25: ['t', 'T', 'ŧ', chr(0x14), None, 't'],
        0x26: ['y', 'Y', '←', chr(0x19), None, 'y'],
        0x27: ['u', 'U', '↓', chr(0x15), None, 'u'],
        0x28: ['i', 'I', '→', chr(0x09), None, 'i'],
        0x29: ['o', 'O', 'ø', chr(0x0F), None, 'o'],
        0x2A: ['p', 'P', 'þ', chr(0x10), None, 'p'],
        0x2B: ['[', ']', '~', chr(0x1D)],
        0x2C: ['\\', '|', '~', chr(0x1C)],
        0x2D: [chr(0x0D), chr(0x0D), '', ''],  # ENTER
        # ROW 3
        0x11: ['a', 'A', 'æ', chr(0x01), None, 'a'],
        0x12: ['s', 'S', 'ſ', chr(0x13), None, 's'],
        0x13: ['d', 'D', 'ð', chr(0x04), None, 'd'],
        0x14: ['f', 'F', 'đ', chr(0x06), None, 'f'],
        0x15: ['g', 'G', 'ŋ', chr(0x07), None, 'g'],
        0x16: ['h', 'H', 'ħ', chr(0x08), None, 'h'],
        0x17: ['j', 'J', '.', chr(0x0A), None, 'j'],
        0x18: ['k', 'K', 'ĸ', chr(0x0B), None, 'k'],
        0x19: ['l', 'L', 'ł', chr(0x0C), None, 'l'],
        0x1A: [';', ':', '˝', ''],
        0x1B: ['\'', '"', '^', chr(0x1B)],
        0x1C: ['{', '}', '’', chr(0x1D)],
        # ROW 4
        0x0e: ['<', '>', '|', ''],
        0x01: ['z', 'Z', '»',  chr(0x1A), None, 'z'],
        0x02: ['x', 'X', '«',  chr(0x18), None, 'x'],
        0x03: ['c', 'C', '¢',  chr(0x03), None, 'c'],
        0x04: ['v', 'V', '„',  chr(0x16), None, 'v'],
        0x05: ['b', 'B', '“”', chr(0x02), None, 'b'],
        0x06: ['n', 'N', '”',  chr(0x0E), None, 'n'],
        0x07: ['m', 'M', 'µ',  chr(0x0D), None, 'm'],
        0x08: [',', '<', '·', '',         None, ','],
        0x09: ['.', '>', '…', '',         None, '.'],
        0x0a: ['/', '?', '–', chr(0x1F)],
        # ROW 5
        0x0F: [' ', ' ', '', chr(0x00)],  # SPACE BAR


        # TEXT EDIT MODE KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        0x4b: [chr(0x1B), chr(0x1B), chr(0x1B), '', ''], #insert?
        # 0x4c: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'F'], # end works, DUP on kb
        # 0x62: [chr(0x1B), chr(0x1B), chr(0x1B), '', ''], # blank
        0xc: [chr(0x1b), chr(0x1b), chr(0x1b), '', chr(0x7F)], # delete line
        # 0x6c: [chr(0x1b), chr(0x1b), chr(0x1b), '', ''], #
        # 0x57: [chr(0x1B), chr(0x1B), chr(0x1B), '', ''], #
        # 0x6c

        # ARROW KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        0x71: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'A'],  # UP ARROW
        0x72: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'D'],  # LEFT ARROW
        # TBD CENTER ARROW
        0x73: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'C'],  # RIGHT ARROW
        0x70: [chr(0x1B), chr(0x1B), chr(0x1B), '', 'B'],  # DOWN ARROW

        # NUMPAD KEYS BLOCK MAPPINGS
        # KEYS FROM TOP TO BOTTOM AND FROM LEFT TO RIGHT
        # ROW 1 (ALL BLANK)
        # 0x1D is in the position of Num Lock on a 101 key keyboard,
        # so do nothing with it
        0x1E: ['/', '/', '', ''],
        0x4F: ['*', '*', '', ''],
        0x50: ['-', '-', '', ''],
        # ROW 2
        0x47: ['7', '7', '', ''],
        # NUMPAD 8  EXTRA UP ARROW
        0x48: ['8', '8', chr(0x1B), chr(0x1B), 'A'],
        0x49: ['9', '9', '', ''],
        0x7B: ['+', '+', '', ''],
        # ROW 3
        # NUMPAD 4   EXTRA LEFT ARROW
        0x44: ['4', '4', chr(0x1B), chr(0x1B), 'D'],
        0x45: ['5', '5', '', ''],
        0x46: ['6', '6', '', '', 'C'],  # NUMPAD 6 EXTRA RIGHT ARROW
        # ROW 4
        0x41: ['1', '1', '', ''],
        # NUMPAD 2  EXTRA DOWN ARROW
        0x42: ['2', chr(0x1B), chr(0x1B), '', 'B'],
        0x43: ['3', '3', '', ''],
        0x2D: [chr(0x0D), '', '', ''],  # ENTER
        # ROW 5
        0x40: ['0', '0', '', ''],
        0x4A: ['.', '', '', ''],

        # Custom character conversions, from ASCII char to EBCDIC code that
        # will override the DEFAULT_CODEPAGE conversions
        'CUSTOM_CHARACTER_CONVERSIONS': {
        },
    },

    # ENTER HERE YOUR ADDITIONAL SCANCODE MAPPINGS

}

# Add a scancode mapping variant which requires use of the custom
# terminfo file.
#
# Use dict() to make a copy.
scancodeDictionaries["122KEY_EN_CUSTOM"] = dict(scancodeDictionaries["122KEY_EN"])
# Send the delete character for the Backspace key as is done by most
# modern terminals (e.g. xterm) rather than sending ^H.  This is
# useful in GNU Emacs so that Ctrl-H can be used to request help.  See
# also https://github.com/inmbolmie/5250_usb_converter/issues/19  As
# noted in that issue, generally it doesn't seem to be necessary for
# this to match what is set in the terminfo description - what is set
# via 'stty' seems to be what matters - so it would probably be
# reasonably safe to apply this setting directly to 122KEY_EN instead
# of adding this new scancode map.
scancodeDictionaries["122KEY_EN_CUSTOM"][0x3D] = [chr(0x7F), chr(0x7F), '', '']


# Max commands pending to send to 5251 in command queue (flow control)
COMMAND_QUEUE_MAX_PENDING = 50

# 5250 commands
# Not all available commands are used here
CLEAR = int('10010', 2)
EOQ = int('1100010', 2)
INSERT_CHARACTER = int('00011', 2)
LOAD_ADDRESS_COUNTER = int('10101', 2)
LOAD_CURSOR_REGISTER = int('10111', 2)
LOAD_REFERENCE_COUNTER = int('00111', 2)
MOVE_DATA = int('00110', 2)
POLL = int('10000', 2)
ACK = int('110000', 2)
READ_ACTIVATE = int('0', 2)
WRITE_ACTIVATE = int('1', 2)
READ_DATA = int('01000', 2)
READ_FIELD_IMMEDIATE = int('11001', 2)
READ_REGISTERS = int('11100', 2)
READ_TO_END_OF_LINE = int('01010', 2)
RESET = int('00010', 2)
SET_MODE = int('10011', 2)
WRITE_CONTROL_DATA = int('00101', 2)
WRITE_CONTROL_DATA_INDICATORS = int('1000101', 2)
WRITE_DATA_LOAD_CURSOR = int('10001', 2)
WRITE_DATA_LOAD_CURSOR_INDICATORS = int('1010001', 2)
WRITE_IMMEDIATE_DATA = int('11101', 2)
RESET_MSR = int('10010010', 2)
RESET_LIGHT_PEN = int('10100010', 2)


# Start of pseudo-terminal management code

# Copyright Notice for (some of) the pseudo-terminal management code
# https://github.com/wildfoundry/dataplicity-agent

# Copyright (c) 2011 Joshua D. Bartlett
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# The following escape codes are xterm codes.
# See http://rtfm.etla.org/xterm/ctlseq.html for more.
START_ALTERNATE_MODE = \
    set('\x1b[?{0}h'.format(i) for i in ('1049', '47', '1047'))
END_ALTERNATE_MODE = \
    set('\x1b[?{0}l'.format(i) for i in ('1049', '47', '1047'))
ALTERNATE_MODE_FLAGS = tuple(START_ALTERNATE_MODE) + tuple(END_ALTERNATE_MODE)


def findlast(s, substrs):
    '''
    Finds whichever of the given substrings occurs last in the given string
    and returns that substring, or returns None if no such strings occur.
    '''
    i = -1
    result = None
    for substr in substrs:
        pos = 0
        try:
            pos = s.decode().rfind(substr)
        except UnicodeDecodeError:
            continue
        if pos > i:
            i = pos
            result = substr
    return result


# This class does the actual work of the pseudo terminal. The spawn() function
# is the main entrypoint.
class Interceptor(object):

    def __init__(self, terminal, termAddress):
        self.master_fd = None
        self.term = terminal
        self.ttypid = None
        self.termAddress = termAddress
        global disableInputCapture
        global term
        global inputQueue, outputCommandQueue, outputQueue

    def restart(self):
        if self.ttypid is not None:
            os.kill(self.ttypid, signal.SIGTERM)
            debugLog.write("SHELL KILLED: " +
                           str(self.termAddress) + "\n")
        self.master_fd = None
        self.ttypid = None
        return

    def spawn(self, argv=None):
        '''
        Create a spawned process.
        Based on the code for pty.spawn().
        '''
        if self.master_fd is not None:
            self.restart()
        if not argv:
            argv = [login_command]

        pid, master_fd = pty.fork()
        self.master_fd = master_fd
        if pid == pty.CHILD:
            os.environ["TERM"] = "vt52"
            # Scripts which check for the following variable should
            # probably just check that it's non-empty in case some
            # more information about the terminal is supplied via it
            # in the future.
            os.environ["TWINAXTERM"] = "y"

            os.execlp(argv[0], *argv)
        else:
            self.ttypid = pid
        # Code for direct capture of STDIN commented. Can be discommented for
        # debugging
        # If you do so keystrokes in the controller window will go directly to
        # the addressed terminal

        # old_handler = signal.signal(signal.SIGWINCH, self._signal_winch)
        # try:
        #     mode = tty.tcgetattr(pty.STDIN_FILENO)
        #     tty.setraw(pty.STDIN_FILENO)
        #     restore = 1
        # except tty.error:    # This is the same as termios.error
        #     restore = 0

        restore = 0
        self._init_fd()
        try:
            self._copy()
        except (IOError, OSError):
            term[self.termAddress].reset()
            debugLog.write("TERMINAL RESET DUE TO SPAWN ERROR: " +
                           str(termAddress) + "\n")
            self.restart()

            if restore:
                tty.tcsetattr(pty.STDIN_FILENO, tty.TCSAFLUSH, mode)

        os.close(master_fd)
        self.master_fd = None

    def _init_fd(self):
        '''
        Called once when the pty is first set up.
        '''
        self._set_pty_size()

    def _signal_winch(self, signum, frame):
        '''
        Signal handler for SIGWINCH - window size has changed.
        '''
        self._set_pty_size()

    def _set_pty_size(self):
        '''
        Sets the window size of the child pty based on the window size of our
        own controlling terminal.
        '''
        assert self.master_fd is not None

        # Get the terminal size of the real terminal, set it on the
        # pseudoterminal.
        buf = array.array('h', [24, 80, 0, 0])
        # fcntl.ioctl(pty.STDOUT_FILENO, termios.TIOCGWINSZ, buf, True)
        fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, buf)

    def _copy(self):
        '''
        Main select loop. Passes all data to self.master_read() or
        self.stdin_read().
        '''
        assert self.master_fd is not None
        master_fd = self.master_fd
        time.sleep(1)
        while 1:
            try:
                rfds, wfds, xfds = select.select(
                    [master_fd, pty.STDIN_FILENO], [], [])
            except select.error as e:
                if e[0] == 4:   # Interrupted system call.
                    continue
            # Read data from shell if it is available and there aren't many
            # pending commands in queue (flow control)
            q_size = outputCommandQueue[self.term.getStationAddress()].qsize()
            if master_fd in rfds and (q_size < COMMAND_QUEUE_MAX_PENDING) and \
                    self.term.getInitialized():
                try:
                    data = os.read(self.master_fd, 128)
                except (IOError, OSError, TypeError):
                    term[self.termAddress].reset()
                    debugLog.write("TERMINAL RESET DUE TO COPY ERROR: " +
                                   str(self.termAddress) + "\n")
                    self.restart()
                    return
                if data is not None:
                    self.master_read(data)
                '''
                Called when there is data to be sent from the child process
                back to the user.
                '''
            if not disableInputCapture and pty.STDIN_FILENO in rfds:
                data = os.read(pty.STDIN_FILENO, 1024)
                self.stdin_read(data.decode())

    def master_read(self, data):
        '''
        Called when there is data to be sent from the child process back to
        the user.
        '''
        flag = findlast(data, ALTERNATE_MODE_FLAGS)
        if flag is not None:
            if flag in START_ALTERNATE_MODE:
                # This code is executed when the child process switches the
                # terminal into alternate mode. The line below assumes that
                # the user has opened vim, and writes a message.
                self.write_master('IEntering special mode.\x1b')
            elif flag in END_ALTERNATE_MODE:
                # This code is executed when the child process switches the
                # terminal back out of alternate mode. The line below assumes
                # that the user has returned to the command prompt.
                self.write_master('echo "Leaving special mode."\r')
        self.write_stdout(data.decode('utf-8', 'ignore'))

    def write_stdout(self, data):
        '''
        Writes to stdout as if the child process had written the data.
        '''
        # os.write(pty.STDOUT_FILENO, data.encode())
        global readLog
        global debugIO
        if debugIO:
            readLog.write(data.encode())

        self.term.txStringWithEscapeChars(data)
        return

    def stdin_read(self, data):
        '''
        Called when there is data to be sent from the user/controlling terminal
        down to the child process.
        '''
        self.write_master(data)

    def write_master(self, data):
        '''
        Writes to the child process from its controlling terminal.
        '''
        master_fd = self.master_fd
        if master_fd is None:
            term[self.termAddress].reset()
            debugLog.write("TERMINAL RESET DUE TO WRITE ERROR: " +
                           str(self.termAddress) + "\n")
            self.restart()
            return
        global writeLog
        global debugIO
        if debugIO:
            writeLog.write(data.encode())
        while data != '':
            n = os.write(master_fd, data.encode())
            data = data[n:]

    def arranque(self, _passarg):
        self.spawn()
        return

# End of pseudo-terminal management code


# Start of serial USB port management code


# Copyright Notice for (some of) the serial USB port management code
# https://github.com/wiseman/arduino-serial
#
#
# Copyright 2007 John Wiseman <jjwiseman@yahoo.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

time.sleep(1)

BPS_SYMS = {
    4800: termios.B4800,
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
    230400: termios.B230400
}

# Indices into the termios tuple.

IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6


def bps_to_termios_sym(bps):
    return BPS_SYMS[bps]


# Routine to initialize USB-serial port
def openSerial(port, speed):
    print("Connecting to 5250 converter USB Device at " + port)
    fd = None
    try:
        fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
    except FileNotFoundError:
        print("The 5250 converter USB Device was not found at " + port +
              ". Run the application with -t DEVICE to use a different one")
        os.kill(os.getpid(), signal.SIGKILL)
        sys.exit()

    attrs = termios.tcgetattr(fd)
    bps_sym = bps_to_termios_sym(speed)
    # Set I/O speed.
    attrs[ISPEED] = bps_sym
    attrs[OSPEED] = bps_sym

    # Black magic from the Arduino serial monitor to initialize serial port
    # c_iflags=0, c_oflags=0x4, c_cflags=0xcbd, c_lflags=0xa30
    attrs[IFLAG] = 0
    attrs[OFLAG] = 0x04
    attrs[CFLAG] = 0xCBD
    attrs[LFLAG] = 0xA30

    termios.tcsetattr(fd, termios.TCSANOW, attrs)

    #Black magic needed for Ubuntu WSL under Windows 10
    try:
        fcntl.ioctl(fd, termios.TIOCMBIS,  '\x02\x00\x00\x00' )
        fcntl.ioctl(fd, termios.TIOCMBIS,   '\x04\x00\x00\x00' )
    except OSError as e:
        if e.errno == errno.EINVAL:
            # This occurs if port isn't a real serial interface.
            # Ignore it so that PTYs may be used for testing purposes.
            print("Ignoring ioctl() failure for TIOCMBIS (only required for "
                  "WSL)")
        else:
            raise e
    termios.tcflush(fd, termios.TCIFLUSH)

    # Configure non-blocking I(O)
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    return fd


def decodeStatusResponse(response):
    """Decode a POLL response from the terminal"""
    # Ej: 0101 1100 0100 0111  not initialized  RAW: 1011100001111000
    # Ej: 0000 0000 0100 1111  initialized after set mode command
    # RAW: 1000000011111000

    status = StatusResponse()

    statusWordA = int.from_bytes(
        response[0].encode(), byteorder='big') & 0x3F
    # 01 1100
    statusWordB = int.from_bytes(
        response[1].encode(), byteorder='big') & 0x1F
    # 0 0111

    statusWord = (reverseByte(statusWordB) << 3) + \
        (reverseByte(statusWordA) >> 2)
    # 11100001110

    # debugLog.write ("DECODED STATUS BYTE A " +
    # str(reverseByte(statusWordA)) + "\n")
    # debugLog.write ("DECODED STATUS BYTE B " +
    # str(reverseByte(statusWordB)) + "\n")
    # debugLog.write ("DECODED STATUS WORD " + str(statusWord) + "\n")
    # 10000000
    status.setStationAddress((statusWord & 0x700) >> 8)
    status.setOutstandingStatus((statusWord & 0x10) >> 4)
    status.setResponseLevel((statusWord & 0x01))

    status.setBusy((statusWord & 0x80) >> 7)
    status.setExceptionStatus((statusWord & 0xE) >> 1)

    status.setLineParity((statusWord & 0x40) >> 6)

    return status


def decodeDataResponse(response):
    """Decode a data response from the terminal (essentially a
    scancode)
    """
    dataWordA = int.from_bytes(
        response[0].encode(), byteorder='big') & 0x3F
    dataWordB = int.from_bytes(
        response[1].encode(), byteorder='big') & 0x18

    return (reverseByte(dataWordB) << 3) + (reverseByte(dataWordA) >> 2)


# Class that controls the serial port (USB) for send and receive
class SerialPortControl:

    # Wait for responses from terminals and invoke their processing
    def waitResponse(self, serialPort, pushToInputQueue, terminal):
        global debugLog
        global term
        global debugConnection
        while True:
            fds, wfds, xfds = select.select([serialPort], [], [], 1)
            if serialPort in fds:
                ans = serialPort.readline()
                if "\n" not in ans:
                    debugLog.write("ERROR, INCOMPLETE LINE: " + ans + "\n")

                ans = ans.replace('\r', '').replace('\n', '')
                while not ans or "EOTX" not in ans:
                    if "DEBUG" in ans:
                        debugLog.write(self.randomString(8) + " " + ans + "\n")
                    elif len(ans) > 0:
                        if debugConnection:
                            debugLog.write("RECEIVED: " + ans + "\n")
                        if pushToInputQueue:
                            inputQueue[terminal].put(ans + "\n")
                    ans = serialPort.readline()
                    ans = ans.replace('\r', '').replace('\n', '')

                if "EOTX" in ans:
                    if debugConnection:
                        debugLog.write("[EOTX]" + "\n")
                    return True

                debugLog.write("ERROR, NOT EOTX RECEIVED" + "\n")
                return False
            else:
                debugLog.write("ERROR, NOT EOTX RECEIVED" + "\n")
                return False
        return

    # Send commands to the terminals
    def write(self, _passarg):
        global outputQueue
        global inputQueue
        global outputCommandQueue
        global term
        global debugLog
        global ttyfile
        fd = openSerial(ttyfile, 57600)
        time.sleep(1)  # wait for Arduino
        serialPort = os.fdopen(fd, "r")
        serialPortWrite = os.fdopen(fd, "w")
        # Loop to write to serial interface

        lastmicros = [None] * 7
        lastmicrosresponse  = [None] * 7
        # Repeat forever
        while True:

            # iterate through initialized terminals
            for terminal in term:
                if terminal is not None:

                    # Management of low speed polling
                    # It seems a real 5251 can handle as much polling as it
                    # can be throw at it but some emulated terminals will have
                    # a bad day if we poll them too much so in that case we
                    # will specify a minimum polling interval
                    if lastmicros[terminal.getStationAddress()] is None:
                        lastmicros[terminal.getStationAddress()] = 0

                    actmicros = int(round(time.time_ns() / 1000));

                    if actmicros < lastmicros[terminal.getStationAddress()] + terminal.getPollDelayUs():
                        continue
                    lastmicros[terminal.getStationAddress()] = actmicros

                    #debugLog.write("POLL AT: " + str(actmicros) + "\n")

                    #Dead terminal detection
                    if term[terminal.getStationAddress()].getInitialized():
                        if lastmicrosresponse[terminal.getStationAddress()] is not None:
                            if actmicros > lastmicrosresponse[terminal.getStationAddress()] + 10000000:
                                debugLog.write("TERMINAL DISCONNECTED: " +
                                               str(terminal.getStationAddress()) + "\n")
                                term[terminal.getStationAddress()].reset()
                                inputQueue[terminal.getStationAddress()].queue.clear();
                                outputCommandQueue[terminal.getStationAddress()].queue.clear();
                                outputQueue[terminal.getStationAddress()].queue.clear();

                                debugLog.write("TERMINAL RESET DUE TO DISCONNECTION: " +
                                               str(terminal.getStationAddress()) + "\n")
                                interceptors[terminal.getStationAddress()].restart()



                    # time.sleep(0.001)

                    # Default action to keep session alive is to poll
                    # continously
                    if (not term[terminal.getStationAddress()].getPollActive()):
                        terminal.POLL()
                        term[terminal.getStationAddress()].setPollActive(0)
                    else:
                        terminal.ACK()
                        term[terminal.getStationAddress()].setPollActive(0)

                    if not outputQueue[terminal.getStationAddress()].empty():
                        towrite = outputQueue[terminal.getStationAddress()].get(
                        )
                        if debugConnection:
                            debugLog.write("WRITING POLL:" + towrite)
                        serialPortWrite.write(towrite)
                    # TBI
                    while not self.waitResponse(serialPort, 1, terminal.getStationAddress()):
                        # Retry
                        debugLog.write("RETRYING POLL: " + towrite + "\n")
                        serialPortWrite.write(towrite)

                    if not inputQueue[terminal.getStationAddress()].empty():
                        lastmicrosresponse[terminal.getStationAddress()] = int(round(time.time_ns() / 1000))
                        self.processResponse(terminal.getStationAddress())

                    doNotSendCommands = 0
                    if not outputQueue[terminal.getStationAddress()].empty():
                        # debugLog.write ("ACK\n")
                        towrite = outputQueue[terminal.getStationAddress()].get(
                        )
                        if debugConnection:
                            debugLog.write("WRITING ACK:" + towrite)
                        serialPortWrite.write(towrite)
                        while not self.waitResponse(serialPort, 1, terminal.getStationAddress()):
                            # Retry
                            debugLog.write("RETRYING ACK: " + towrite + "\n")
                            serialPortWrite.write(towrite)
                        if not inputQueue[terminal.getStationAddress()].empty():
                            #term[terminal.getStationAddress()].setPollActive(0)
                            self.processResponse(terminal.getStationAddress())
                        else:
                            doNotSendCommands = 1

                    # if outputCommandQueue[terminal].empty():
                        # wait a little not to trash too much CPU as we are
                        # not in a hurry
                        # time.sleep(0.01)

                    # debugLog.write ("COMMANDS " +str(outputCommandQueue.empty()) + " " + str(term.getBusy())  + "\n")

                    if (not outputCommandQueue[terminal.getStationAddress()].empty()) and (not terminal.getBusy()) and not doNotSendCommands:
                        #debugLog.write ("SENDING " + str(outputCommandQueue[terminal.getStationAddress()].qsize())  + " COMMANDS\n")
                        while not outputCommandQueue[terminal.getStationAddress()].empty():
                            element = outputCommandQueue[terminal.getStationAddress()].get()
                            if element == "":
                                # self.processResponse()
                                break
                            else:
                                if debugConnection:
                                    debugLog.write("WRITING COMMAND:" + element)
                                serialPortWrite.write(element)
                                while not self.waitResponse(serialPort, 0, terminal.getStationAddress()):
                                    # Retry
                                    debugLog.write("RETRYING: " + element + "\n")
                                    serialPortWrite.write(element)

        return

    # Utility to generate random string to keep log lines correlation when
    # needed for debugging purposes
    def randomString(self, stringLength=4):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    # Process response from a terminal
    # essentially status and scancodes
    def processResponse(self, terminal):
        # global the5250log
        global inputQueue, outputCommandQueue, outputQueue
        global term
        global debugLog
        global debugKeystrokes
        global debugConnection
        if not inputQueue[terminal].empty():
            # Get poll status and keystrokes
            # Generally we won't be reading anything from the terminal other
            # than polling statuses
            # So this logic is very simplified
            firstWord = inputQueue[terminal].get()
            # the5250log.write(firstWord)
            status = decodeStatusResponse(firstWord)

            if debugConnection:
                id = self.randomString()
                debugLog.write(id + " RECEIVED STATUS WORD: " + firstWord)
                debugLog.write(id + "   stationAddress: " +
                               str(status.getStationAddress()) + "\n")
                debugLog.write(id + "   busy: " + str(status.getBusy()) + "\n")
                debugLog.write(id + "   outstandingStatus: " +
                               str(status.getOutstandingStatus()) + "\n")
                debugLog.write(id + "   exceptionStatus: " +
                               str(status.getExceptionStatus()) + "\n")
                debugLog.write(id + "   responseLevel: " +
                               str(status.getResponseLevel()) + "\n")
                debugLog.write(id + "   lineParity: " +
                               str(status.getLineParity()) + "\n")

            term[terminal].setBusy(status.getBusy())

            term[terminal].setLineParity(status.getLineParity())

            term[terminal].setPollActive(1);

            hasSecondWord = False;

            if not inputQueue[terminal].empty():
                secondWord = inputQueue[terminal].get()
                hasSecondWord = True

            if inputQueue[terminal].empty() and \
                    (status.getExceptionStatus() == 7):
                # Terminal detected but needs to be initialized

                # Reset terminal

                term[terminal].setInitialized(0)
                inputQueue[terminal].queue.clear();
                outputCommandQueue[terminal].queue.clear();
                outputQueue[terminal].queue.clear();
                debugLog.write("TERMINAL RESET BEFORE INITIALIZATION: " +
                               str(terminal) + "\n")
                interceptors[terminal].restart()


                # Wait for it do die
                time.sleep(1)

                # If we get only 1 byte we are in unitialized state, we have
                # to send
                # a SET_MODE command to iniatize the terminal
                if debugConnection:
                    debugLog.write("SETTING MODE\n")
                term[terminal].SET_MODE()

                return

            elif (status.getExceptionStatus() == 0 and \
                    not term[terminal].getInitialized() and \
                    not status.getBusy()):
                # Clear screen and init shell
                term[terminal].setInitialized(1)
                debugLog.write("STARTING SHELL FOR DETECTED TERMINAL: " +
                               str(terminal) + "\n")
                term[terminal].ESC_E()
                _thread.start_new_thread(
                    interceptors[terminal].arranque, (None,))

                if not term[terminal].getResponseLevel() == \
                        status.getResponseLevel():
                    term[terminal].setResponseLevel(
                        status.getResponseLevel())
                return

            elif status.getExceptionStatus() != 0 and \
                    term[terminal].getInitialized():
                # Exception, log and send a reset command

                debugLog.write("TERMINAL:" + str(terminal) +
                               " SENT AN EXCEPTION CODE: " +
                               str(status.getExceptionStatus()) + "\n")
                term[terminal].resetException()
            elif status.getExceptionStatus() == 0 and term[terminal].getInitialized():
                if hasSecondWord:
                    if len(secondWord) >= 2:
                        if debugConnection:
                            debugLog.write("RECEIVED DATA WORD: " + secondWord)
                        # the5250log.write(secondWord)
                        scancode = decodeDataResponse(secondWord)
                        # debugLog.write ("RECEIVED DATA BYTE: " +
                        # str(scancode) + "\n")
                        # get keystroke if ack is not pending and is different
                        # from 0x00 and 0xFF
                        # debugLog.write ("CANDIDATE SCANCODE: " +
                        # hex(scancode) + " RLEVEL: " +
                        # str(term.getResponseLevel()) + "\n")
                        if ((not term[terminal].getResponseLevel() ==
                                status.getResponseLevel()) and
                                (scancode != 0x00) and (scancode != 0xFF)):
                            term[terminal].setResponseLevel(
                                status.getResponseLevel())
                            if debugKeystrokes:
                                debugLog.write("RECEIVED SCANCODE: " +
                                               hex(scancode) +
                                               " FROM TERMINAL: " +
                                               str(terminal) + "\n")
                            # Convert scancode and send to the SHELL
                            if scancode != "":
                                # Send to SHELL
                                term[terminal].processScanCode(scancode)
                        if not term[terminal].getResponseLevel() == \
                                status.getResponseLevel():
                            term[terminal].setResponseLevel(
                                status.getResponseLevel())

            # Send ACK if it is needed to indicate to the 5250 we have read
            # its status
            #if (not term[terminal].getBusy()) and term[terminal].getPollActive():
            #    # debugLog.write ("SENDING ACK " + str(term.getForceAck()) +
            #    # " " + str(term.getPollActive()) + "\n")
            #    term[terminal].ACK()
            #    return

        return

# End of serial USB port management code


# Class to hold the status decoded from a POLL response
class StatusResponse():
    def __init__(self):
        self.stationAddress = 0
        self.busy = 0
        self.outstandingStatus = 0
        self.exceptionStatus = 0
        self.responseLevel = 0
        self.lineParity = 0
        return

    def getStationAddress(self):
        return self.stationAddress

    def setStationAddress(self, value):
        self.stationAddress = value
        return

    def getBusy(self):
        return self.busy

    def setBusy(self, busy):
        self.busy = busy
        return

    def getOutstandingStatus(self):
        return self.outstandingStatus

    def setOutstandingStatus(self, value):
        self.outstandingStatus = value
        return

    def getExceptionStatus(self):
        return self.exceptionStatus

    def setExceptionStatus(self, value):
        self.exceptionStatus = value
        return

    def getResponseLevel(self):
        return self.responseLevel

    def setResponseLevel(self, value):
        self.responseLevel = value
        return

    def getLineParity(self):
        return self.lineParity

    def setLineParity(self, value):
        self.lineParity = value
        return


# Command line interface for debugging
#
class MyPrompt(cmd.Cmd):
    prompt = '5250> '
    use_rawinput = False
    global debugConnection;
    intro = "Welcome! Type ? to list commands"

    def __init__(self):
        cmd.Cmd.activeTerminal = defaultActiveTerminal
        super().__init__()
        return

    def __init__(self, file):
        cmd.Cmd.activeTerminal = defaultActiveTerminal
        super(MyPrompt, self).__init__(stdin=file, stdout=file)
        return

    def do_exit(self, inp):
        print("Bye")
        return True

    def do_restartterminal(self, addr):
        interceptors[int(addr)].restart()
        time.sleep(2)
        term[int(addr)].ESC_E()
        _thread.start_new_thread(interceptors[int(addr)].arranque, (None,))
        return

    def do_setactiveterminal(self, addr):
        try:
            if term[int(addr)] is None:
                print("Error, the specified terminal '" + addr + "' isn't initialized")
                return
            cmd.Cmd.activeTerminal = int(addr)
            return
        except ValueError:
            print("Invalid terminal")
            return


    def do_getactiveterminal(self,inp):
        print("The currently active terminal is: " + str(cmd.Cmd.activeTerminal) )
        return

    def do_input(self, inp):
        global interceptors
        interceptors[cmd.Cmd.activeTerminal].stdin_read(inp + "\n")

    def do_inputspc(self, inp):
        global interceptors
        interceptors[cmd.Cmd.activeTerminal].stdin_read(inp + " ")
        return

    def do_ctrlkey(self, string):

        ctrlscancode = term[cmd.Cmd.activeTerminal].scancodeDictionary['CTRL_PRESS'][0]
        term[cmd.Cmd.activeTerminal].processScanCode(ctrlscancode)

        for i in range(0, len(string)):
            for key, value in term[cmd.Cmd.activeTerminal].scancodeDictionary.items():
                try:
                    if value[0] == string[i]:
                        term[cmd.Cmd.activeTerminal].processScanCode(key)
                except:
                    pass
        if len(term[cmd.Cmd.activeTerminal].scancodeDictionary['CTRL_RELEASE']):
            ctrlscancode = term[cmd.Cmd.activeTerminal].scancodeDictionary['CTRL_RELEASE'][0]
            term[cmd.Cmd.activeTerminal].processScanCode(ctrlscancode)
        return

    def do_altkey(self, string):

        ctrlscancode = term[cmd.Cmd.activeTerminal].scancodeDictionary['ALT_PRESS'][0]
        term[cmd.Cmd.activeTerminal].processScanCode(ctrlscancode)

        for i in range(0, len(string)):
            for key, value in term[cmd.Cmd.activeTerminal].scancodeDictionary.items():
                try:
                    if value[0] == string[i].lower():
                        term[cmd.Cmd.activeTerminal].processScanCode(key)
                except:
                    pass
        # Release if enabled
        if len(term[cmd.Cmd.activeTerminal].scancodeDictionary['ALT_RELEASE']):
            ctrlscancode = term[cmd.Cmd.activeTerminal].scancodeDictionary['ALT_RELEASE'][0]
            term[cmd.Cmd.activeTerminal].processScanCode(ctrlscancode)
        return

    def do_txstring(self, string):
        term[cmd.Cmd.activeTerminal].txString(string)
        return

    def do_txebcdic(self, string):
        """Send or more data bytes to display.

        For example, to output "HI" in inverse video, issue either of the
        following commands:
          txebcdic 0x21 0xC8 0xC9 0x20
          txebcdic 33 200 201 32
        """
        ebcdicArray = bytearray()
        for word in string.split():
            ebcdicArray.append(int(word, base=0))
        term[cmd.Cmd.activeTerminal].txEbcdic(ebcdicArray)

    def do_txchartable(self, string):
        """Output a character table showing glyphs and attributes.

        The table is in column-major order for consistency with IBM
        documents.
        """
        CLEAR_ATTRIBUTES = 0x20
        SPACE = 0x40

        t = term[cmd.Cmd.activeTerminal]
        t.CR()
        t.LF()
        for row in range(0, 16):
            for col in range(16):
                char = col << 4 | row
                if col in [2, 3]: # char is an attribute
                    t.txEbcdic([char])
                    t.txString(f"{char:02X}")
                    t.txEbcdic([CLEAR_ATTRIBUTES, SPACE])
                else:
                    t.txString(f" {char:02X}:")
                    t.txEbcdic([char])
            t.CR()
            t.LF()

    def do_cr(self, inp):
        term[cmd.Cmd.activeTerminal].CR()
        return

    def do_lf(self, inp):
        term[cmd.Cmd.activeTerminal].LF()
        return

    # VT52 commands

    def do_escE(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_E()
        return

    def do_escB(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_B()
        return

    def do_escL(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_L()
        return

    def do_escM(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_M()
        return

    def do_escH(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_H()
        return

    def do_esce(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_e()
        return

    def do_escf(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_f()
        return

    def do_escp(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_p()
        return

    def do_escq(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_q()
        return

    def do_escJ(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_J()
        return

    def do_escK(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_K()
        return

    def do_escl(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_l()
        return

    def do_esco(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_o()
        return

    def do_escd(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_d()
        return

    def do_escw(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_w()
        return

    def do_escv(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_v()
        return

    def do_escD(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_D()
        return

    def do_escC(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_C()
        return

    def do_escA(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_A()
        return

    def do_escY(self, inp):
        global term
        (x, y) = inp.split()
        term[cmd.Cmd.activeTerminal].ESC_Y(int(x), int(y))
        return

    def do_escb(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_b()
        return

    def do_escj(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_j()
        return

    def do_escI(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_I()
        return

    def do_esck(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_k()
        return

    def do_escc(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].ESC_c()
        return

    def do_LF(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].LF()
        return

    def do_CR(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].CR()
        return

    def do_BS(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].BS()
        return

    def do_BEL(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].BEL()
        return

    def do_FF(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].FF()
        return

    def do_HT(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].HT()
        return

    def do_VT(self, inp):
        global term
        term[cmd.Cmd.activeTerminal].VT()
        return

    def do_getcursor(self, inp):
        print("XPOS: " + str(term.cursorX) + "\n")
        print("YPOS: " + str(term.cursorY) + "\n")
        print("BUFFERPOS: " + str(term.getEncodedCursorPosition()) + "\n")
        return

    def do_txstatusbyte(self, status):
        term[cmd.Cmd.activeTerminal].transmitCommand(
            WRITE_CONTROL_DATA, term[cmd.Cmd.activeTerminal].destinationAddr,
            [int(status)])
        term[cmd.Cmd.activeTerminal].EOQ()
        return

    def do_txstatusbyte2(self, status):
        """Send a Write Control Data command with two data frames, as is
        supported since the 3180 Model 2.

        Supply only the value to be included in the second data frame,
        in decimal.
        """
        t = term[cmd.Cmd.activeTerminal]
        t.transmitCommand(
            WRITE_CONTROL_DATA, t.destinationAddr,
            [t.statusByte | 0x40, int(status)])
        t.EOQ()
        return

    def do_txindicatorsbyte(self, status):
        term[cmd.Cmd.activeTerminal].transmitCommand(
            WRITE_DATA_LOAD_CURSOR_INDICATORS,
            term[cmd.Cmd.activeTerminal].destinationAddr, [int(status)])
        term[cmd.Cmd.activeTerminal].EOQ()
        return

    def do_txindicatorsbyte347x(self, status):
        """Control the indicators that were first introduced on 3476 and 3477.

        Provide a value in decimal to be included in the first data
        frame.  There is no support for sending the second data frame.
        """
        status = int(status)
        if status & 0x01 != 0:
            print("LSB (indicating frame 2 is present) must not be set")
            return
        term[cmd.Cmd.activeTerminal].transmitCommand(
            WRITE_CONTROL_DATA_INDICATORS,
            term[cmd.Cmd.activeTerminal].destinationAddr, [status])
        term[cmd.Cmd.activeTerminal].EOQ()
        return

    def do_txchar(self, char):
        piece = bytearray()
        piece.insert(0, int(char, 0))
        piece.insert(0, 1)
        term[cmd.Cmd.activeTerminal].transmitCommand(WRITE_DATA_LOAD_CURSOR, term[cmd.Cmd.activeTerminal].destinationAddr, piece)
        term[cmd.Cmd.activeTerminal].incrementCursor(1)
        term[cmd.Cmd.activeTerminal].EOQ()
        return

    def do_sendscancode(self, code):
        term[cmd.Cmd.activeTerminal].processScanCode(int(code, 16))
        return

    def do_tx(self, inp):
        print("Transmitting '{}'".format(inp))
        global outputCommandQueue
        outputCommandQueue[cmd.Cmd.activeTerminal].put(inp + "\n")
        outputCommandQueue[cmd.Cmd.activeTerminal].put("")
        return

    def do_decodeStringData(self, inp):
        print("TRANSLATING:" + str(inp) + " " + str(len(inp)) + "\n")
        for i in range(0, len(inp), 2):

            dataWordA = int.from_bytes(inp[i].encode(), byteorder='big') & 0x3F
            dataWordB = int.from_bytes(
                inp[i + 1].encode(), byteorder='big') & 0x3
            resultado = (dataWordB << 6) + (dataWordA)
            print("RESULTADO: " + str(inp[i]) + " " +
                  str(inp[i + 1]) + " " + str(resultado) + "\n")
        return

    def do_EOF(self, inp):
        return

    def do_enabledebug(self,inp):
        global debugConnection
        debugConnection = True;
        return

    def do_disabledebug(self,inp):
        global debugConnection
        debugConnection = False;
        return

    def do_python(self, _):
        """Enter a Python interpreter (read-eval-print loop).

        Note: Interaction with terminals using this interpreter is
        timing-sensitive due to the use of threads, e.g. this has the
        same effect as the 'txebcdic' example:

          b = bytearray([4, 33, 200, 201, 32])
          term[0].transmitCommand(WRITE_DATA_LOAD_CURSOR, 0, b); term[0].EOQ()

        but invoking the two statements on the second line with a
        delay between them results in the EOQ command never being
        sent.
        """
        code.interact(local=globals(),
                      banner="""\
Interactive Python interpreter (read-eval-print loop)
'help' for help, Ctrl-D to return to CLI""",
                      exitmsg="Returning from Python interpreter to CLI")


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


def reverseByte(byte):
    return int('{:08b}'.format(byte)[::-1], 2)


# Class that implments the VT52 to 5250 conversion and holds the terminal
# status. There will be one instance of this class for each running terminal
class VT52_to_5250():
    def __init__(self, address, scancodeDictionary, pollDelayUs,
                 EBCDICcodepage, advancedFeatures, clickerEnabled ):
        self.pollDelayUs = pollDelayUs
        self.EBCDICcodepage = EBCDICcodepage
        self.destinationAddr = address
        self.scancodeDictionary = scancodeDictionaries[scancodeDictionary]
        self.cursorX = 0
        self.cursorY = 0
        self.savedCursorX = 0
        self.savedCursorY = 0
        self.busy = 1
        self.lineParity = 0
        self.responseLevel = 0
        self.isInExceptionState = 0
        self.isShiftEnabled = 0
        self.isControlEnabled = 0
        self.isAltEnabled = 0
        self.isExtraEnabled = 0
        self.forceAck = 0
        self.pollActive = 0
        self.initialized = 0
        self.newlinePending = 0
        self.cursorInPreviousLine = 0
        self.savedNewlinePending = 0
        self.savedCursorInPreviousLine = 0
        self.incompleteSequence = bytearray()
        self.clickerEnabled = clickerEnabled
        self.advancedFeatures = advancedFeatures
        self.statusByte = 0
        # Meaning of each statusByte bits:
        # 0x80 Hide cursor
        # 0x40 ???? unknown ATM
        # 0x20 Enable cursor blink
        # 0x10 Enable text blink
        # 0x08 Reverse video
        # 0x04 Reset exception status
        # 0x02 Disable keyboard clicker (solenoid) but no solenoid, no fun...
        # 0x01 Bell, audible alert. Very loud indeed
        if not self.clickerEnabled:
            self.statusByte = 0x02
        self.indicatorsByte = 0
        # Meaning of each indicatorsBye bits:
        # 0x80 Highest light on
        # 0x40
        # 0x20
        # 0x10
        # 0x08
        # 0x04
        # 0x02
        # 0x01 Lowest light on
        self.isCapsLockEnabled = 0
        return

    def reset(self):
        self.cursorX = 0
        self.cursorY = 0
        self.savedCursorX = 0
        self.savedCursorY = 0
        self.busy = 1
        self.lineParity = 0
        self.responseLevel = 0
        self.isInExceptionState = 0
        self.isShiftEnabled = 0
        self.isControlEnabled = 0
        self.isAltEnabled = 0
        self.isExtraEnabled = 0
        self.forceAck = 0
        self.pollActive = 0
        self.initialized = 0
        self.newlinePending = 0
        self.cursorInPreviousLine = 0
        self.savedNewlinePending = 0
        self.savedCursorInPreviousLine = 0
        self.incompleteSequence = bytearray()
        self.statusByte = 0
        # Meaning of each statusByte bits:
        # 0x80 Hide cursor
        # 0x40 ???? unknown ATM
        # 0x20 Enable cursor blink
        # 0x10 Enable text blink
        # 0x08 Reverse video
        # 0x04 Reset exception status
        # 0x02 Disable keyboard clicker (solenoid) but no solenoid, no fun...
        # 0x01 Bell, audible alert. Very loud indeed
        if not self.clickerEnabled:
            self.statusByte = 0x02
        self.indicatorsByte = 0
        # Meaning of each indicatorsBye bits:
        # 0x80 Highest light on
        # 0x40
        # 0x20
        # 0x10
        # 0x08
        # 0x04
        # 0x02
        # 0x01 Lowest light on
        self.isCapsLockEnabled = 0
        return

    # Various getters and setters
    def toggleEnabledClicker(self):
        if self.clickerEnabled:
            self.clickerEnabled = False
            self.statusByte = self.statusByte | 0x02
        else:
            self.clickerEnabled = True
            self.statusByte = self.statusByte & 0xFD
        # tx to terminal
        self.transmitCommand(WRITE_CONTROL_DATA, self.destinationAddr, [
                             self.statusByte])
        self.EOQ()
        return

    def getStationAddress(self):
        return self.destinationAddr

    def getPollDelayUs(self):
        return self.pollDelayUs

    def setInitialized(self, value):
        self.initialized = value
        return

    def getInitialized(self):
        return self.initialized

    def getPollActive(self):
        return self.pollActive

    def setPollActive(self, status):
        self.pollActive = status
        return

    def getBusy(self):
        return self.busy

    def setBusy(self, state):
        self.busy = state
        return

    def getLineParity(self):
        return self.lineParity

    def setLineParity(self, state):
        self.lineParity = state
        return

    def getResponseLevel(self):
        return self.responseLevel

    def setResponseLevel(self, state):
        self.responseLevel = state
        return

    def getIsInExceptionState(self):
        return self.isInExceptionState

    def setIsInExceptionState(self, state):
        self.isInExceptionState = state
        return

    # Extracts escape chars from string and calls the adequate method to
    # convert them to 5250 commands
    def txStringWithEscapeChars(self, string):
        stringArray = bytearray(string.encode())
        stringToTxArray = bytearray()

        if len(self.incompleteSequence) > 0:
            stringArray = self.incompleteSequence + stringArray
            self.incompleteSequence = bytearray()
            # debugLog.write ("COMPLETING ESCAPE SEQUENCE\n")

        while len(stringArray) > 0:
            character = stringArray.pop(0)
            if character == 0x1b:
                # ESC escape
                if len(stringToTxArray) > 0:
                    # If a escape sequence start is detected we first transmit
                    # the string characters we have already stored
                    self.txString(stringToTxArray.decode())
                    stringToTxArray = bytearray()
                if len(stringArray) == 0:
                    # It seems the escape sequence is incomplete and the rest
                    # will be received in the next string
                    # debugLog.write ("INCOMPLETE ESCAPE SEQUENCE\n")
                    self.incompleteSequence = bytearray()
                    self.incompleteSequence.append(0x1b)
                    continue
                character2 = stringArray.pop(0)

                if character2 == 0x5B:
                    # ANSI sequence
                    if len(stringArray) == 0:
                        # It seems the escape sequence is incomplete and the
                        # rest will be received in the next string
                        # debugLog.write ("INCOMPLETE ANSI ESCAPE SEQUENCE\n")
                        self.incompleteSequence = bytearray()
                        self.incompleteSequence.append(0x1b)
                        self.incompleteSequence.append(0x5B)
                        continue
                    character2 = stringArray.pop(0)
                    if character2 == 0x32:
                        if len(stringArray) == 0:
                            # It seems the escape sequence is incomplete and
                            # the rest will be received in the next string
                            # debugLog.write
                            # ("INCOMPLETE ANSI ESCAPE SEQUENCE\n")
                            self.incompleteSequence = bytearray()
                            self.incompleteSequence.append(0x1b)
                            self.incompleteSequence.append(0x5B)
                            self.incompleteSequence.append(0x32)
                            continue
                        character3 = stringArray.pop(0)
                        if character3 == 0x4A:
                            self.ESC_E()
                            continue

                if character2 == 74:
                    self.ESC_J()
                elif character2 == 75:
                    self.ESC_K()
                elif character2 == 69:
                    self.ESC_E()
                elif character2 == 108:
                    self.ESC_l()
                elif character2 == 111:
                    self.ESC_o()
                elif character2 == 100:
                    self.ESC_d()
                elif character2 == 66:
                    self.ESC_B()
                elif character2 == 72:
                    self.ESC_H()
                elif character2 == 68:
                    self.ESC_D()
                elif character2 == 67:
                    self.ESC_C()
                elif character2 == 65:
                    self.ESC_A()
                elif character2 == 77:
                    self.ESC_M()
                elif character2 == 89:
                    if len(stringArray) == 0:
                        # It seems the escape sequence is incomplete and the
                        # rest will be received in the next string
                        # debugLog.write ("INCOMPLETE ESC_M SEQUENCE\n")
                        self.incompleteSequence = bytearray()
                        self.incompleteSequence.append(0x1b)
                        self.incompleteSequence.append(89)
                        continue
                    character3 = stringArray.pop(0)
                    if len(stringArray) == 0:
                        # It seems the escape sequence is incomplete and the
                        # rest will be received in the next string
                        # debugLog.write ("INCOMPLETE ESC_M SEQUENCE\n")
                        self.incompleteSequence = bytearray()
                        self.incompleteSequence.append(0x1b)
                        self.incompleteSequence.append(89)
                        self.incompleteSequence.append(character3)
                        continue
                    character4 = stringArray.pop(0)
                    self.ESC_Y(character3 - 32, character4 - 32)
                elif character2 == 98:
                    self.ESC_b()
                elif character2 == 76:
                    self.ESC_L()
                elif character2 == 107:
                    self.ESC_k()
                elif character2 == 99:
                    self.ESC_c()
                elif character2 == 113:
                    self.ESC_q()
                elif character2 == 112:
                    self.ESC_p()
                elif character2 == 106:
                    self.ESC_j()
                elif character2 == 73:
                    self.ESC_I()
                elif character2 == 119:
                    self.ESC_w()
                elif character2 == 118:
                    self.ESC_v()
                elif character2 == 101:
                    self.ESC_e()
                elif character2 == 102:
                    self.ESC_f()
                else:
                    # Received something we have not implemented
                    debugLog.write("UNKNOWN ESCAPE CODE: " +
                                   str(character2) + "\n")

            else:
                # Something that is not an escape sequence but needs to be
                # converted to 5250 commands
                if character == 0x0D:
                    # Carru return
                    if len(stringToTxArray) > 0:
                        self.txString(stringToTxArray.decode())
                        stringToTxArray = bytearray()
                    self.CR()
                elif character == 0x0A:
                    # Line feed
                    if len(stringToTxArray) > 0:
                        self.txString(stringToTxArray.decode())
                        stringToTxArray = bytearray()
                    self.LF()
                elif character == 0x09:
                    # Horizontal tabulator
                    if len(stringToTxArray) > 0:
                        self.txString(stringToTxArray.decode())
                        stringToTxArray = bytearray()
                    self.HT()
                elif character == 0x08:
                    # Backspace
                    if len(stringToTxArray) > 0:
                        self.txString(stringToTxArray.decode())
                        stringToTxArray = bytearray()
                    self.BS()
                elif character == 0x07:  # BELL
                    # Bell
                    self.BEL()
                    continue
                else:
                    # Regular ASCII char, store to transmit
                    stringToTxArray.append(character)

        if len(stringToTxArray) > 0:
            self.txString(stringToTxArray.decode())
        return

    def txString(self, string):
        # Converts to EBCDIC and transmits an ASCII string
        ebcdicArray = bytearray()
        for char in string:
            try:
                # Some custom character translations
                if 'CUSTOM_CHARACTER_CONVERSIONS' in self.scancodeDictionary and char in self.scancodeDictionary['CUSTOM_CHARACTER_CONVERSIONS']:
                    ebcdicArray.append(
                        self.scancodeDictionary['CUSTOM_CHARACTER_CONVERSIONS'][char])

                else:
                    ebcdicArray = ebcdicArray + \
                        char.encode(self.EBCDICcodepage)
            except UnicodeEncodeError:
                # In anything goes wrong (strange character or some shit)
                # transmit a blank to keep session on sync
                ebcdicArray = ebcdicArray + " ".encode(self.EBCDICcodepage)
        self.txEbcdic(ebcdicArray)

    def txEbcdic(self, ebcdicArray):
        # Split in chunks of 10 or less so that the string fits into the 5250
        # command buffer
        pieces = chunks(ebcdicArray, 10)
        i = 1
        for piece in pieces:
            i = i+1
            # Check if we are writing over the screen buffer. In that case
            # we need to insert a new line
            if len(piece) > self.getCharsToEndOfScreen():

                # write self.getCharsToEndOfScreen() chars
                first = piece[:self.getCharsToEndOfScreen()]
                second = piece[self.getCharsToEndOfScreen():]

                first2 = bytearray(first)
                first2.insert(0, len(first))
                second2 = bytearray(second)
                second2.insert(0, len(second))

                if len(first) > 0:
                    self.transmitCommand(
                        WRITE_DATA_LOAD_CURSOR, self.destinationAddr, first2)
                    self.incrementCursor(len(first))
                    self.EOQ()

                # write rest of chars
                if len(second) > 0:
                    # delete first line
                    self.cursorX = 0
                    self.cursorY = 0
                    # self.EOQ()
                    self.ESC_M()
                    self.cursorX = 23
                    self.cursorY = 0
                    self.transmitCommand(LOAD_CURSOR_REGISTER,
                                         self.destinationAddr,
                                         self.getEncodedCursorPosition())
                    self.transmitCommand(LOAD_ADDRESS_COUNTER,
                                         self.destinationAddr,
                                         self.getEncodedCursorPosition())
                    self.EOQ()

                    # txstring
                    self.transmitCommand(
                        WRITE_DATA_LOAD_CURSOR, self.destinationAddr, second2)
                    self.incrementCursor(len(second))
                    self.EOQ()

            else:

                # Stuff to manage vt52 weirdness in cursor positioning when
                # writing over the end of line because if no char is written
                # after reaching EOL the cursor is really still in the
                # previous line if we try to move it so we cannot for example
                # insert inmediately a new line at the bottom if we were
                # already in the last line
                if self.newlinePending:
                    # delete first line
                    self.cursorX = 0
                    self.cursorY = 0
                    # self.EOQ()
                    self.ESC_M()
                    self.cursorX = 23
                    self.cursorY = 0
                    self.transmitCommand(LOAD_CURSOR_REGISTER,
                                         self.destinationAddr,
                                         self.getEncodedCursorPosition())
                    self.transmitCommand(LOAD_ADDRESS_COUNTER,
                                         self.destinationAddr,
                                         self.getEncodedCursorPosition())
                    self.EOQ()
                    self.newlinePending = False
                    self.cursorInPreviousLine = False

                setNewLinePending = False
                setCursorInPreviousLine = False

                if len(piece) == self.getCharsToEndOfLine():
                    # Cursor in Vt52 will be in the position x-1,79 regarding
                    # cursor movement
                    setCursorInPreviousLine = True

                if len(piece) == self.getCharsToEndOfScreen():
                    setNewLinePending = True

                piece2 = bytearray(piece)
                piece2.insert(0, len(piece))
                self.transmitCommand(WRITE_DATA_LOAD_CURSOR,
                                     self.destinationAddr, piece2)
                self.incrementCursor(len(piece))
                self.EOQ()

                if setNewLinePending:
                    # Fill just one line without LF
                    self.newlinePending = True

                if setCursorInPreviousLine:
                    # Cursor in Vt52 will be in the position x-1,79 regarding
                    # cursor movement
                    self.cursorInPreviousLine = True

        return

    def transmitCommand(self, command, destination, data):
        return self.transmitCommandOrPoll(command, destination, data, 0)

    def transmitPoll(self, command, destination, data):
        return self.transmitCommandOrPoll(command, destination, data, 1)

    # Encodes a command + data or poll to send over the serial interface
    def transmitCommandOrPoll(self, command, destination, data, isPoll):
        # @todo The destination parameter appears to be redundant and
        # could probably be removed.
        assert destination == self.destinationAddr

        firstByte = (command & 0x3F) + 0x40
        secondByte = ((command & 0xC0) >> 6) + (destination << 2) + 0x40

        if isPoll and self.getLineParity():
            secondByte = secondByte + 0x01

        toTx = bytearray()
        toTx.append(firstByte)
        toTx.append(secondByte)
        index = 1
        for i in data:
            thirdByte = (i & 0x3F) + 0x40
            if thirdByte == 0x7F:
                # weird bug with DEL chars
                thirdByte = 0x3F
            if (index < len(data)):
                fourthByte = ((i & 0xC0) >> 6) + (destination << 2) + 0x40
            else:
                fourthByte = ((i & 0xC0) >> 6) + (7 << 2) + 0x40
            index = index+1
            toTx.append(thirdByte)
            toTx.append(fourthByte)

        toTx.append(0x0A)
        global outputQueue
        if isPoll:
            outputQueue[self.destinationAddr].put(toTx.decode())
        else:
            # debugLog.write("PUSHING COMMAND: " + toTx.decode() + "\n")
            outputCommandQueue[self.destinationAddr].put(toTx.decode())
        # debugLog.write(toTx.decode())
        # debugLog.write("\n")
        return

    # Mark end of a related command sequence
    # At this point the serial code will wait for a response before sending
    # more commands to this terminal
    # to avoid buffer overruns
    def endOfCommandSequence(self):
        outputCommandQueue[self.destinationAddr].put("")
        return

    # Get cursor position in 5250 format  (x*80 + y)
    def getEncodedPosition(self, x, y):
        return (x*80 + y).to_bytes(2, byteorder='big')

    # Increment cursor position without changing line
    def incrementCursorKeepLine(self, inc):
        self.newlinePending = False
        self.cursorInPreviousLine = False
        self.cursorY = min([max([0, self.cursorY + inc]), 79])
        return

    # Increment cursor position changing line if needed
    def incrementCursor(self, inc):
        self.newlinePending = False
        self.cursorInPreviousLine = False
        self.cursorX = min(
            [max([0, (self.cursorX + ((self.cursorY + inc) // 80))]), 23])
        self.cursorY = min([max([0, ((self.cursorY + inc) % 80)]), 79])
        return

    # Get number of characters left to write before we reach the end of screen
    # buffer
    def getCharsToEndOfScreen(self):
        return 1920 - (80*self.cursorX + self.cursorY)

    # Get number of characters left to write before we reach the end of current
    # line
    def getCharsToEndOfLine(self):
        return 80 - self.cursorY

    # Move cursor
    def positionCursor(self, x, y):
        self.newlinePending = False
        self.cursorInPreviousLine = False
        self.cursorX = x
        self.cursorY = y
        return

    # Save current cursor position
    def saveCursorPosition(self):
        self.savedNewlinePending = self.newlinePending
        self.savedCursorInPreviousLine = self.cursorInPreviousLine
        self.savedCursorX = self.cursorX
        self.savedCursorY = self.cursorY
        return

    # Restore saved cursor position
    def restoreCursorPosition(self):
        self.newlinePending = self.savedNewlinePending
        self.cursorInPreviousLine = self.savedCursorInPreviousLine
        self.cursorX = self.savedCursorX
        self.cursorY = self.savedCursorY
        return

    # Tabulator jump
    def jumpCursorNextTab(self):
        self.newlinePending = False
        self.cursorInPreviousLine = False
        self.cursorY = ((self.cursorY + 8) // 8) * 8
        if (self.cursorY > 79):
            self.cursorY = self.cursorY % 80
            self.cursorX = min([23, (self.cursorX + 1)])

    def getLowerRightCornerEncodedPosition(self):
        return self.getEncodedPosition(23, 79)

    def getUpperLeftCornerEncodedPosition(self):
        return self.getEncodedPosition(0, 0)

    def getBeginningCurrentLineEncodedPosition(self):
        return self.getEncodedPosition(self.cursorX, 0)

    def getEndCurrentLineEncodedPosition(self):
        return self.getEncodedPosition(self.cursorX, 79)

    def getLowerRightPenultimateEncodedPosition(self):
        return self.getEncodedPosition(22, 79)

    # Get cursor position in 5250 format
    def getEncodedCursorPosition(self):
        if self.cursorX < 0:
            # What? Go away, nothing to see here
            self.cursorX = 0
        if self.cursorY < 0:
            # WTF? I told you to go away!
            self.cursorY = 0
        return self.getEncodedPosition(self.cursorX, self.cursorY)

    # Get first char of next line position
    def getBeginningNextLineEncodedPosition(self):
        return self.getEncodedPosition(min([self.cursorX + 1, 23]), 0)

    # Position cursor in origin
    def zeroCursorPosition(self):
        self.newlinePending = False
        self.cursorInPreviousLine = False
        self.cursorX = 0
        self.cursorY = 0
        return

    # Process scan code, either setting make/break status or converting to
    # ASCII and sending to the shell
    def processScanCode(self, scancode):
        global interceptors
        # Look for break keys
        if scancode in self.scancodeDictionary['EXTRA']:
            # Next char is extra
            self.isExtraEnabled = 1
            return

        if scancode in self.scancodeDictionary['SHIFT_PRESS']:
            # press shift
            self.isShiftEnabled = 1
            # debugLog.write("SPECIAL SHIFT ENABLED\n")
        elif scancode in self.scancodeDictionary['SHIFT_RELEASE']:
            # release shift
            self.isShiftEnabled = 0
            # debugLog.write("SPECIAL SHIFT DISABLED\n")
        elif scancode in self.scancodeDictionary['CTRL_PRESS']:

            if self.isControlEnabled and \
                    len(self.scancodeDictionary['CTRL_RELEASE']) == 0:
                # needed if you use a non-break key for releasing CONTROL
                self.isControlEnabled = 0
            else:
                # pressed ctrl
                self.isControlEnabled = 1
                # debugLog.write("SPECIAL CONTROL ENABLED\n")
        elif scancode in self.scancodeDictionary['CTRL_RELEASE']:
            # release ctrl
            self.isControlEnabled = 0
            # debugLog.write("SPECIAL CONTROL DISABLED\n")
        elif scancode in self.scancodeDictionary['ALT_PRESS']:
            if self.isAltEnabled and \
                    len(self.scancodeDictionary['ALT_RELEASE']) == 0:
                # needed if you use a non-break key for releasing CONTROL
                self.isAltEnabled = 0
            else:
                # press alt
                self.isAltEnabled = 1
                # debugLog.write("SPECIAL ALT ENABLED\n")
        elif scancode in self.scancodeDictionary['ALT_RELEASE']:
            # release alt
            self.isAltEnabled = 0
            # debugLog.write("SPECIAL ALT DISABLED\n")
        elif scancode in self.scancodeDictionary['CAPS_LOCK']:
            # CAPS LOCK
            self.isCapsLockEnabled = not self.isCapsLockEnabled
            # Turn on light
            if self.isCapsLockEnabled:
                if not self.advancedFeatures:
                    self.indicatorsByte = self.indicatorsByte | 0x20
                    self.transmitCommand(WRITE_DATA_LOAD_CURSOR_INDICATORS,
                                         self.destinationAddr,
                                         [self.indicatorsByte])
                else:
                    self.transmitCommand(WRITE_CONTROL_DATA_INDICATORS,
                                         self.destinationAddr,
                                         [0x80])

            else:
                if not self.advancedFeatures:
                    self.indicatorsByte = self.indicatorsByte & 0xDF
                    self.transmitCommand(WRITE_DATA_LOAD_CURSOR_INDICATORS,
                                         self.destinationAddr,
                                         [self.indicatorsByte])
                else:
                    self.transmitCommand(WRITE_CONTROL_DATA_INDICATORS,
                                         self.destinationAddr,
                                         [0x00])

            self.EOQ()

        else:
            # regular key
            # Transmit regular, shifted, control, or alt variant
            # debugLog.write("RECEIVED SCANCODE:" + hex(scancode) +
            #                " FROM TERMINAL: " +
            #                str(self.destinationAddr)  +   "\n")
            if scancode not in self.scancodeDictionary:
                # error
                # debugLog.write("UNKNOWN SCANCODE: " + str(scancode) +
                #                " FOR TERMINAL: " +
                #                str(self.destinationAddr) + "\n")
                self.isExtraEnabled = 0
                return

            else:
                if \
                        (self.isShiftEnabled and not self.isCapsLockEnabled) \
                        or \
                        (not self.isShiftEnabled and self.isCapsLockEnabled):
                    # SHIFT+key

                    if self.scancodeDictionary[scancode][1] == chr(0x1B):
                        # Cursors
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][1])
                        if len(self.scancodeDictionary[scancode]) > 4:
                            interceptors[self.destinationAddr].stdin_read(
                                self.scancodeDictionary[scancode][4])
                    else:
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][1])

                elif self.isControlEnabled:
                    # CTRL+key
                    if len(self.scancodeDictionary['CTRL_RELEASE']) == 0:
                        # needed if you use a non-break key for CONTROL
                        self.isControlEnabled = 0
                    # Check if ESC + key
                    if self.scancodeDictionary[scancode][3] == chr(0x1B):
                        # Cursors
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][3])
                        if len(self.scancodeDictionary[scancode]) > 4:
                            interceptors[self.destinationAddr].stdin_read(
                                self.scancodeDictionary[scancode][4])
                    else:
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][3])

                elif self.isAltEnabled:

                    # Check for enable/disble solenid
                    if self.scancodeDictionary[scancode][0] == 's':
                        self.toggleEnabledClicker()

                    # Check if ESC + key
                    elif self.scancodeDictionary[scancode][2] == chr(0x1B):
                        # Cursors
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][2])
                        if len(self.scancodeDictionary[scancode]) > 4:
                            interceptors[self.destinationAddr].stdin_read(
                                self.scancodeDictionary[scancode][4])
                    else:
                        # ALT + key
                        if len(self.scancodeDictionary['ALT_RELEASE']) == 0:
                            # needed if you use a non-break key for ALT
                            self.isAltEnabled = 0
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][2])

                elif self.isExtraEnabled:
                    self.isExtraEnabled = 0
                    if len(self.scancodeDictionary[scancode]) > 5:
                        interceptors[self.destinationAddr].stdin_read(
                            chr(0x1B))
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][5])

                else:
                    # Standard key
                    if self.scancodeDictionary[scancode][0] == chr(0x1B):
                        # Cursors
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][0])
                        if len(self.scancodeDictionary[scancode]) > 4:
                            interceptors[self.destinationAddr].stdin_read(
                                self.scancodeDictionary[scancode][4])
                    else:
                        interceptors[self.destinationAddr].stdin_read(
                            self.scancodeDictionary[scancode][0])

        self.isExtraEnabled = 0
        return

    # VT52 escape sequences implemented as 5250 commands and other 5250
    # management commands
    #
    # Clear sc

    def RESET(self):
        # Set transmission mode to zero fill
        self.transmitCommand(RESET, self.destinationAddr, [])
        return

    def SET_MODE(self):
        # Set transmission mode to zero fill
        self.transmitCommand(SET_MODE, self.destinationAddr, [0])
        self.EOQ()
        self.transmitCommand(WRITE_CONTROL_DATA, self.destinationAddr, [
                             self.statusByte])
        self.EOQ()
        return

    def resetException(self):
        self.transmitCommand(WRITE_CONTROL_DATA, self.destinationAddr, [
                             self.statusByte | 0x04])
        self.EOQ()
        return

    def POLL(self):
        # Poll station
        self.transmitPoll(POLL, self.destinationAddr, [])
        return

    def ACK(self):
        # ACK station response
        self.transmitPoll(ACK, self.destinationAddr, [])
        return

    def EOQ(self):
        # End of command queue
        self.transmitCommand(EOQ, self.destinationAddr, [])
        self.endOfCommandSequence()
        return

    def BS(self):
        # Backspace 	Delete character to left of cursor.
        self.incrementCursor(-1)
        # update cursor position
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        self.transmitCommand(WRITE_DATA_LOAD_CURSOR,
                             self.destinationAddr, [1, 0x40])
        self.EOQ()
        return

    def BEL(self):
        # Bell, audible alert
        if self.clickerEnabled:
            self.transmitCommand(WRITE_CONTROL_DATA, self.destinationAddr, [
                                self.statusByte | 0x01])
            self.EOQ()
        return

    def ESC_J(self):
        # Clear to end of screen 	Clear screen from cursor onwards.
        # Move address counter to cursor position
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        # Move reference counter to lower right corner
        self.transmitCommand(LOAD_REFERENCE_COUNTER, self.destinationAddr,
                             self.getLowerRightCornerEncodedPosition())
        # Send clear command
        self.transmitCommand(CLEAR, self.destinationAddr, [])
        self.EOQ()
        return

    def ESC_K(self):
        # Clear to end of line 	Clear line from cursor onwards.
        # Move address counter to cursor position
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        # Move reference counter to end of current line
        self.transmitCommand(LOAD_REFERENCE_COUNTER, self.destinationAddr,
                             self.getEndCurrentLineEncodedPosition())
        # Send clear command
        self.transmitCommand(CLEAR, self.destinationAddr, [])
        self.EOQ()
        return

    def ESC_E(self):
        # Clear screen 	Clear screen and place cursor at top left corner.
        # Move address counter to upper left corner
        self.transmitCommand(LOAD_ADDRESS_COUNTER, self.destinationAddr,
                             self.getUpperLeftCornerEncodedPosition())
        # Move reference counter to lower right corner
        self.transmitCommand(LOAD_REFERENCE_COUNTER, self.destinationAddr,
                             self.getLowerRightCornerEncodedPosition())
        # Send clear command
        self.transmitCommand(CLEAR, self.destinationAddr, [])
        # Move cursor to upper left corner
        self.zeroCursorPosition()
        # update cursor position
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        return

    def ESC_l(self):
        # Clear line 	Clear current line.
        # Move address counter to beginning of current line
        self.transmitCommand(LOAD_ADDRESS_COUNTER, self.destinationAddr,
                             self.getBeginningCurrentLineEncodedPosition())
        # Move reference counter to end of current line
        self.transmitCommand(LOAD_REFERENCE_COUNTER, self.destinationAddr,
                             self.getEndCurrentLineEncodedPosition())
        # Send clear command
        self.transmitCommand(CLEAR, self.destinationAddr, [])
        # Move cursor to beginiing lina
        self.transmitCommand(LOAD_CURSOR_REGISTER, self.destinationAddr,
                             self.getBeginningCurrentLineEncodedPosition())
        self.EOQ()
        return

    def ESC_o(self):
        # Clear to start of line 	Clear current line up to cursor.
        # Move address counter to beginning of current line
        self.transmitCommand(LOAD_ADDRESS_COUNTER, self.destinationAddr,
                             self.getBeginningCurrentLineEncodedPosition())
        # Move reference counter to cursor position
        self.transmitCommand(LOAD_REFERENCE_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        # Send clear command
        self.transmitCommand(CLEAR, self.destinationAddr, [])
        self.EOQ()
        return

    def ESC_d(self):
        # Clear to start of screen 	Clear screen up to cursor.
        # Move address counter to upper left corner
        self.transmitCommand(LOAD_ADDRESS_COUNTER, self.destinationAddr,
                             self.getUpperLeftCornerEncodedPosition())
        # Move reference counter to cursor position
        self.transmitCommand(LOAD_REFERENCE_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        # Send clear command
        self.transmitCommand(CLEAR, self.destinationAddr, [])
        self.EOQ()
        return

    def ESC_B(self):
        # Cursor down 	Move cursor one line downwards.
        # increment cursor line
        if self.cursorX > 0 and self.cursorInPreviousLine:
            self.cursorY = 79

        elif self.cursorX < 23:
            self.cursorX = self.cursorX + 1

        # update cursor position
        self.positionCursor(self.cursorX, self.cursorY)
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()

        return

    def ESC_H(self):
        # Cursor home 	Move cursor to the upper left corner.
        # zero cursor position
        self.zeroCursorPosition()
        # update cursor position
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        return

    def ESC_D(self):
        # Cursor left 	Move cursor one column to the left.
        if self.cursorX > 0 and self.cursorInPreviousLine:
            if not self.newlinePending:
                self.cursorX = self.cursorX - 1
            self.cursorY = 79
        elif self.cursorInPreviousLine:
            self.cursorY = 79
        # decremento cursor column
        self.incrementCursorKeepLine(-1)
        # update cursor position
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        return

    def ESC_C(self):
        # Cursor right 	Move cursor one column to the right.

        if self.cursorX > 0 and \
                self.cursorInPreviousLine and \
                not self.newlinePending:
            self.cursorX = self.cursorX - 1

        if self.cursorInPreviousLine:
            self.cursorY = 79

        # increment cursor column
        self.incrementCursorKeepLine(1)
        # update cursor position
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        return

    def ESC_A(self):
        # Cursor up 	Move cursor one line upwards.
        # decrement cursor line
        if self.cursorX > 0:
            if self.cursorInPreviousLine:
                if not self.newlinePending:
                    self.cursorX = self.cursorX - 1
                self.cursorY = 79
            self.cursorX = self.cursorX - 1
            # update cursor position
            self.positionCursor(self.cursorX, self.cursorY)
            self.transmitCommand(LOAD_CURSOR_REGISTER,
                                 self.destinationAddr,
                                 self.getEncodedCursorPosition())
            self.transmitCommand(LOAD_ADDRESS_COUNTER,
                                 self.destinationAddr,
                                 self.getEncodedCursorPosition())
            self.EOQ()
        return

    def ESC_Y(self, x, y):
        # Set cursor position 	Position cursor.
        self.positionCursor(x, y)
        # update cursor position
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        return

    def ESC_b(self):
        # Foreground color 	Set text colour.
        return

    def ESC_L(self):
        # Insert line 	Insert a line and move cursor to beginning
        # Move lines one position to the bottom
        # Hide cursor.
        hidden = False
        if not self.statusByte & 0x80:
            hidden = True
            self.statusByte = self.statusByte | 0x80
            self.transmitCommand(WRITE_CONTROL_DATA,
                                 self.destinationAddr, [self.statusByte])
            self.EOQ()

        # for x in range(23, self.cursorX, -1):
        self.transmitCommand(LOAD_REFERENCE_COUNTER,
                             self.destinationAddr,
                             self.getEncodedPosition(23, 79))
        # Move reference counter to beginning of current line
        self.transmitCommand(LOAD_CURSOR_REGISTER, self.destinationAddr,
                             self.getEncodedPosition(self.cursorX, 0))
        # Move cursor counter to end of screen
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedPosition(22, 79))
        # Move data
        self.transmitCommand(MOVE_DATA, self.destinationAddr, [])
        # update cursor position
        self.EOQ()

        # Cursor to first column
        self.incrementCursorKeepLine(-80)
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        # Clear current line
        self.ESC_K()
        # Restore cursor
        if hidden:
            self.statusByte = self.statusByte & 0x7F
            self.transmitCommand(WRITE_CONTROL_DATA,
                                 self.destinationAddr, [self.statusByte])
        self.EOQ()
        return

    def ESC_M(self):
        # Delete line 	Remove line position cursor first column.
        # Hide cursor.
        hidden = False
        if not self.statusByte & 0x80:
            hidden = True
            self.statusByte = self.statusByte | 0x80
            self.transmitCommand(WRITE_CONTROL_DATA,
                                 self.destinationAddr, [self.statusByte])
            self.EOQ()

        if self.cursorX != 23:
            # copy previous line
            self.transmitCommand(LOAD_REFERENCE_COUNTER,
                                 self.destinationAddr,
                                 self.getEncodedPosition(self.cursorX, 0))
            # Move reference counter to beginning of current line
            self.transmitCommand(LOAD_ADDRESS_COUNTER,
                                 self.destinationAddr,
                                 self.getEncodedPosition(self.cursorX + 1, 0))
            # Move cursor counter to end of screen
            self.transmitCommand(LOAD_CURSOR_REGISTER,
                                 self.destinationAddr,
                                 self.getEncodedPosition(23, 79))
            # Move data
            self.transmitCommand(MOVE_DATA, self.destinationAddr, [])
            # update cursor position
            self.EOQ()

        # Clear last line
        # delete last line
        # Move address counter to beginning of last line
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedPosition(23, 0))
        # Move reference counter to end of last line
        self.transmitCommand(LOAD_REFERENCE_COUNTER,
                             self.destinationAddr,
                             self.getEncodedPosition(23, 79))
        # Send clear command
        self.transmitCommand(CLEAR, self.destinationAddr, [])
        self.EOQ()

        # Cursor to first column
        self.incrementCursorKeepLine(-80)
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        # Restore cursor
        if hidden:
            self.statusByte = self.statusByte & 0x7F
            self.transmitCommand(WRITE_CONTROL_DATA,
                                 self.destinationAddr, [self.statusByte])
            self.EOQ()
        return

    def LF(self):
        # Line feed 	Line feed.
        if (self.cursorX == 23):
            # Last line
            prevCursorY = self.cursorY
            # Need to delete line
            # delete first line
            self.cursorX = 0
            self.cursorY = 0
            self.ESC_M()
            self.cursorX = 23
            self.cursorY = prevCursorY
            self.transmitCommand(LOAD_CURSOR_REGISTER,
                                 self.destinationAddr,
                                 self.getEncodedCursorPosition())
            self.transmitCommand(LOAD_ADDRESS_COUNTER,
                                 self.destinationAddr,
                                 self.getEncodedCursorPosition())
            self.EOQ()
        else:
            # Otherwise
            self.incrementCursor(80)
            self.transmitCommand(LOAD_CURSOR_REGISTER,
                                 self.destinationAddr,
                                 self.getEncodedCursorPosition())
            self.transmitCommand(LOAD_ADDRESS_COUNTER,
                                 self.destinationAddr,
                                 self.getEncodedCursorPosition())
            self.EOQ()
        return

    def ESC_k(self):
        # Restore cursor position 	Restore saved cursor.
        self.restoreCursorPosition()
        # update cursor position
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        return

    def ESC_c(self):
        # Background color 	Set background colour.
        return

    def CR(self):
        # Carriage Return 	Move cursor to the start of the line.
        if self.newlinePending:
            # Already made
            return
        if self.cursorInPreviousLine and self.cursorX > 0:
            self.cursorX = self.cursorX - 1
        self.incrementCursorKeepLine(-80)
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()

        return

    def ESC_q(self):
        # Normal video 	Switch off inverse video text.
        self.statusByte = self.statusByte & 0xF7
        self.transmitCommand(WRITE_CONTROL_DATA,
                             self.destinationAddr, [self.statusByte])
        self.EOQ()
        return

    def ESC_p(self):
        # Reverse video 	Switch on inverse video text.
        self.statusByte = self.statusByte | 0x08
        self.transmitCommand(WRITE_CONTROL_DATA,
                             self.destinationAddr, [self.statusByte])
        self.EOQ()
        return

    def ESC_j(self):
        # Save cursor position 	"Remember" cursor.
        self.saveCursorPosition()
        return

    def ESC_I(self):
        # Cursor up and insert 	Move cursor one line upwards and scroll.
        if (self.cursorX == 0):
            self.ESC_L()
        self.ESC_A()
        return

    def FF(self):
        # Formfeed 	Form feed.
        ESC_E()
        return

    def HT(self):
        # Tabulator 	Horizontal tabulator.

        # Calculate cursor Position
        self.jumpCursorNextTab()
        self.transmitCommand(LOAD_CURSOR_REGISTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.transmitCommand(LOAD_ADDRESS_COUNTER,
                             self.destinationAddr,
                             self.getEncodedCursorPosition())
        self.EOQ()
        return

    def VT(self):
        # Tabulator 	Vertical tabulator
        LF()
        return

    def ESC_w(self):
        # Wrap off 	Disable line wrap.
        # TBD
        return

    def ESC_v(self):
        # Wrap on 	Enable line wrap.
        # TBD
        return

    def ESC_e(self):
        # Cur_on 	Show cursor.
        self.statusByte = self.statusByte & 0x7F
        self.transmitCommand(WRITE_CONTROL_DATA,
                             self.destinationAddr, [self.statusByte])
        self.EOQ()
        return

    def ESC_f(self):
        # Cur_off 	Hide cursor.
        self.statusByte = self.statusByte | 0x80
        self.transmitCommand(WRITE_CONTROL_DATA,
                             self.destinationAddr, [self.statusByte])
        self.EOQ()
        return

    def Blink_on(self):
        # Switch on cursor blinking.
        self.statusByte = self.statusByte | 0x20
        self.transmitCommand(WRITE_CONTROL_DATA,
                             self.destinationAddr, [self.statusByte])
        self.EOQ()
        return

    def Blink_off(self):
        # Switch off cursor blinking.
        self.statusByte = self.statusByte & 0xDF
        self.transmitCommand(WRITE_CONTROL_DATA,
                             self.destinationAddr, [self.statusByte])
        self.EOQ()
        return

    def Set_blink(self):
        # Set blink rate.
        # TBD
        return

    def Get_blink(self):
        # Inquire blink rate.
        # TBD
        return


#Launches Cmd attached to a file
def spawnCmd(file, connection):
        MyPrompt(file).cmdloop()
        if connection is not None:
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()


# Listens for connections in TCP port 5251 ;-) and launches a Cmd for each
def telnetServer():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(True)
    s.bind(('', 5251))
    s.listen(5)
    print(f"Making Telnet socket available at port 5251")
    print(f"Use e.g. `$ telnet localhost 5251` to connect.")

    while True:
        try:
            connection, address = s.accept()
            connection.setblocking(True)
            _thread.start_new_thread(spawnCmd, (connection.makefile(mode="rw"),connection))

        except BlockingIOError:
            pass



# Listens at UDS socket for CMD connections
def udsServer():
    spath = "/tmp/5250_cmd_sock"
    try:
        if stat.S_ISSOCK(os.stat(spath).st_mode):
            os.remove(spath)
        else:
            print(f"Path '{spath}' exists but is not a socket. Exiting")
            sys.exit(1)
    except FileNotFoundError:
        pass

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(spath)
    s.listen(1)
    print(f"Making UDS socket available at {spath}.")
    print(f"Use e.g. `$ socat stdio UNIX:{spath}` to connect.")

    while True:
        cs, ca = s.accept()
        _thread.start_new_thread(spawnCmd, (cs.makefile(mode="rw"),cs))


def parseTermDef(arg):
    """Parse and return a single terminal definition from the command line."""
    termdef = arg.split(":")

    termAddress = int(termdef[0])
    termDictionary = DEFAULT_SCANCODE_DICTIONARY
    pollDelayUs = DEFAULT_SLOW_POLLING
    codepage = DEFAULT_CODEPAGE
    advancedFeatures = DEFAULT_FEATURES

    if len(termdef) > 1 and termdef[1]!="":
        termDictionary = termdef[1]

    if len(termdef) > 2 and termdef[2]!="":
        value = termdef[2]
        SUFFIX = "us"

        def raiseParseError():
            raise argparse.ArgumentTypeError(
                f'"{value}" is not a valid slow poll or poll delay value: '
                f'must be a non-negative value in microseconds with a '
                f'"{SUFFIX}" suffix (e.g. "650us"), "0" for 0us, "1" for '
                f'{SLOW_POLL_MICROSECONDS}us, or "2" for '
                f'{ULTRA_SLOW_POLL_MICROSECONDS}us')

        if value == "0":
            pollDelayUs = 0
        elif value == "1":
            pollDelayUs = SLOW_POLL_MICROSECONDS
        elif value == "2":
            pollDelayUs = ULTRA_SLOW_POLL_MICROSECONDS
        else:
            if not value.endswith(SUFFIX):
                raiseParseError()
            number = value[:-1 * len(SUFFIX)]

            try:
                number = int(number)
            except ValueError:
                raiseParseError()

            if number < 0:
                raiseParseError()

            pollDelayUs = number

    if len(termdef) > 3 and termdef[3]!="":
        codepage = termdef[3]

    if len(termdef) > 4 and termdef[4]!="":
        advancedFeatures = bool(int(termdef[4]))

    return (termAddress, termDictionary, pollDelayUs, codepage, advancedFeatures)


def parseArgs():
    """Parse and return command-line arguments"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "terminals",
        metavar="TERM-DEFINITION",
        help="Terminal definition(s) of the form STATION_ADDRESS"
             "[:[SCANCODE_DICT]"
             "[:[SLOW_POLL]"
             "[:[EBCDIC_CODEPAGE]"
             "[:[EXTRA_FEATURES]]]]]",
        type=parseTermDef, nargs="*",
        # Default action is to look for
        # terminal address = DEFAULT_STATION_ADDRESS
        default=[parseTermDef(str(DEFAULT_STATION_ADDRESS))])
    parser.add_argument(
        "-c", dest="debugConnection", action="store_true",
        help="Enable extra connection debugging (default: disabled)")
    parser.add_argument(
        "-i", dest="debugIO", action="store_true",
        help="Enable debugging of input/output from terminal (default: "
             "disabled)")
    parser.add_argument(
        "-k", dest="debugKeystrokes", action="store_true",
        help="Enable keystroke scancode debug (default: disabled)")

    if DEFAULT_KEYBOARD_CLICKER_ENABLED:
        clicker_default = "enabled"
    else:
        clicker_default = "disabled - option has no effect"
    parser.add_argument(
        "-s", dest="clickerEnabled", action="store_false",
        help=f"Disable keyboard clicker (default: {clicker_default})")

    parser.add_argument(
        "-t", metavar="TTY-FILE", dest="ttyfile", default="/dev/ttyACM0",
        help="Use the given TTY device file (default: %(default)s)")
    parser.add_argument(
        "-l", "--login", metavar="PATH", default="etc/twinax_login_default",
        help="Login/shell executable (default: %(default)s)")
    parser.add_argument(
        "-u", dest="udsSocket", action="store_true",
        help="Enable Unix Domain Socket (default: disabled)")
    parser.add_argument(
        "-p", dest="telnetSocket", action="store_true",
        help="Enable Telnet Service at port 5251 (default: disabled)")
    parser.add_argument(
        "-d", dest="daemon", action="store_true",
        help="Enable daemon mode (default: disabled)")

    args = parser.parse_args()

    if not os.access(args.login, os.X_OK):
        parser.error(f"The login/shell {args.login} does not exist or is not "
                     f"executable")

    return args


# Main method
if __name__ == '__main__':

    term = [None] * 7
    interceptors = [None] * 7
    inputQueue = [None] * 7
    outputQueue = [None] * 7
    outputCommandQueue = [None] * 7
    debugKeystrokes = False
    debugIO = False
    debugConnection = False
    ttyfile = None
    defaultActiveTerminal = None
    login_command = False


    args = parseArgs()
    if args.debugConnection:
        print("Enabling connection debug\n")
        debugConnection = True

    if args.debugIO:
        print("Enabling I/O debug\n")
        debugIO = True

    if args.debugKeystrokes:
        print("Enabling scancode debug\n")
        debugKeystrokes = True

    clickerEnabled = DEFAULT_KEYBOARD_CLICKER_ENABLED
    if DEFAULT_KEYBOARD_CLICKER_ENABLED and not args.clickerEnabled:
        print("Disabling keyboard clicker\n")
        clickerEnabled = False

    print(f"Using tty device at: {args.ttyfile}\n")
    ttyfile = args.ttyfile

    login_command = args.login

    for (termAddress, termDictionary, pollDelayUs, codepage, advancedFeatures) \
        in args.terminals:

        print("Searching for terminal address: " + str(termAddress) +
              "; with scancode dictionary: " + termDictionary +
              f"; slow poll interval: {pollDelayUs}us" +
              "; EBCDIC codepage: " + codepage +
              "; advanced features: " + str(advancedFeatures) + "\n")

        # Initializing terminal "termAddress"

        # Communication queues for the terminal
        inputQueue[termAddress] = queue.Queue()
        outputQueue[termAddress] = queue.Queue()
        outputCommandQueue[termAddress] = queue.Queue()
        # Terminal conversion object
        term[termAddress] = VT52_to_5250(
            termAddress, termDictionary, pollDelayUs, codepage, advancedFeatures, clickerEnabled)
        # Interceptor that spawns a VT52 shell and manages info from/to it
        interceptors[termAddress] = Interceptor(term[termAddress], termAddress)
        # Set active terminal if none defined
        if defaultActiveTerminal is None:
            defaultActiveTerminal = termAddress

    writeLog = None
    readLog = None
    debugLog = None

    if args.daemon:
        debugLog = open("/tmp/debug.log", "w", buffering=1)
    else:
       debugLog = open("debug.log", "w", buffering=1)
       if debugIO:
           writeLog = open("write.log", "wb", buffering=0)
           readLog = open("read.log", "wb", buffering=0)



    debugLog.write("COMMAND LINE: " + ' '.join(sys.argv) + "\n")
    # the5250log = open("5250.log","w", buffering=1)

    # Run serial port controller in its own thread
    serialController = SerialPortControl()
    _thread.start_new_thread(serialController.write, (None,))

    disableInputCapture = 1

    if args.udsSocket:
        print("Enabling Unix Domain Socket\n")
        #Launch thread to accept UDS CMD connections
        _thread.start_new_thread(udsServer, ())

    if args.telnetSocket:
        print("Enabling Telnet Service at port 5251\n")
        #Launch thread to accept telnet CMD connections
        _thread.start_new_thread(telnetServer, ())

    #Launch CMD for the main shell
    if args.daemon:
        print("Enabling daemon mode\n")
        try:
            while True:
                time.sleep(1)
        except (SystemExit,KeyboardInterrupt):
            pass
    else:
        MyPrompt(None).cmdloop()
        os.remove(spath)
