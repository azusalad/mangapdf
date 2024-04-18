# Matches the number after Ch.
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
# Background color
PAGE_NUM_FILL = (0, 0, 0, 127)
# Text color
PAGE_NUM_COLOR = (255, 255, 255)
# Padding
PAGE_PADDING = 1
# Font size
PAGE_SIZE = 20

# ----------------------------
# Defaults
# Arguments will take priority over defaults below
# ----------------------------
# Delete temporary pdf files created during conversion
DELETE = True
