# Regex pattern for matching the chapter number given the chapter title name.
# The first matching group is the chapter number.
# This pattern currently matches the number after Ch.
REGEX_PATTERN = "^.+Ch\.(\d+)(\s|$)(.+$|)"

# ----------------------------
# Title page
# ----------------------------
TITLE_FONT = "Arial.TTF"
TITLE_SIZE = 40
TITLE_WIDTH = 1354
TITLE_HEIGHT = 1920
TITLE_BG_COLOR = "white"
TITLE_TEXT_COLOR = "black"

# ----------------------------
# Page numbers
# ----------------------------
PAGE_FONT = "Arial.TTF"
# 0: top left
# 1: top right
# 2: bottom left
# 3: bottom right
PAGE_LOCATION = 1
# Background color (R, G, B, A)
PAGE_NUM_FILL = (0, 0, 0, 127)
# Text color (R, G, B)
PAGE_NUM_COLOR = (255, 255, 255)
# Padding
PAGE_PADDING = 1
# Font size
PAGE_SIZE = 30

# ----------------------------
# Defaults
# Arguments will take priority over defaults below
# ----------------------------
# Delete temporary pdf files created during conversion
DELETE = True
# Remove margins or whitespace.  Useful for 4-Koma
TRIM = True
# Apply ocrmypdf on output pdf
OCR = False
OCR_LANGUAGES = "eng"

# If no title argument given, the default will be the basename of the output path
TITLE = None
AUTHOR = None
