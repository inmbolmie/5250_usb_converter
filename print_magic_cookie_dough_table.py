#!/usr/bin/env python3

"""Print a table of available attributes using "magic cookie dough" characters

Consider writing the output of this script to a file to support
copying-and-pasting the Unicode escape sequences or literal characters:

    python3 print_magic_cookie_dough_table.py > attributes.txt

The literal characters are in the columns labelled with "*"s.

"""

import sys

# Attribute byte values accepted by the 5250-series terminal:
ATTRIBUTE_MIN = 0x20
ATTRIBUTE_COUNT = 0x20

# The code point of the magic cookie dough character:
MAGIC_COOKIE_MIN = 0x000F5220

# Magic cookie dough characters used to format the table:
CLEAR_ATTRS = chr(MAGIC_COOKIE_MIN)
TITLE_ATTR = chr(MAGIC_COOKIE_MIN - ATTRIBUTE_MIN + 0x24)

# Dimensions of the printed table:
COLS = 4
ROWS = ATTRIBUTE_COUNT // COLS

# It's probably useful for one of these to have a descender:
SAMPLE_TEXT = "Wq"

print("U=Underline  I=Intensity  R=Reverse video")

key_row_2 = (
    r"\Uxxxxxxxx=Unicode character escape (xxxxxxxx=Unicode code point)"
)
# Put TITLE_ATTR at the end of this line so that:
# - it takes effect from the first character on the title row; and
# - when viewed outside of 5250_terminal.py, the fact that it is wider
#   than an ASCII character doesn't affect column alignment.
print(f"{key_row_2:79}{TITLE_ATTR}")

# Include full-width (as opposed to ASCII, which are half-width)
# characters in the title row in columns where magic cookie dough
# characters appear in the body of the table.  This ensures that when
# the output is viewed outside of 5250_terminal.py, columns are still
# aligned.  When viewed in 5250_terminal.py, this will just be a
# blank.
WIDE_PAD = "\U000f00f0"
print(
    f"       "
    f"|(normal)    {WIDE_PAD}  {WIDE_PAD}"
    f"|Blink       {WIDE_PAD}  {WIDE_PAD}"
    f"|ColSep      {WIDE_PAD}  {WIDE_PAD}"
    f"|Blink+ColSep{WIDE_PAD}  {WIDE_PAD}{CLEAR_ATTRS}"
)

row_titles = [
    " - - - ",
    " - - R ",
    " - I - ",
    " - I R ",
    " U - - ",
    " U - R ",
    " U I - ",
    "Ignored",
]
assert len(row_titles) == ROWS

for row, row_title in enumerate(row_titles):
    sys.stdout.write(f"{row_title}| ")
    for col in range(COLS):
        attr = ATTRIBUTE_MIN + col * ROWS + row
        code_point = attr - ATTRIBUTE_MIN + MAGIC_COOKIE_MIN
        sys.stdout.write(
            f"\\U{code_point:08X} "
            f"{chr(code_point)}{SAMPLE_TEXT}{CLEAR_ATTRS}"
        )
        if col < COLS - 1:
            sys.stdout.write("| ")
    sys.stdout.write("\n")
