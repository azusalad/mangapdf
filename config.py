# Regex pattern for matching the chapter number given the chapter title name.
# The first matching group is the chapter number.
# This pattern currently matches the number after Ch.
REGEX_PATTERN = r"^.+Ch\.(\d+|\d+.\d)(\s|$)(.+$|)"

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
# Trim Margins
# ----------------------------
# Remove margins or whitespace.  Useful for 4-Koma
TRIM = True
# Pixels equal to this or under will be set to 0 when finding bounding box
# Higher values give more aggressive trimming
TRIM_THRESHOLD = 20
# The color of the margins in (R, G, B).  Set to None to use the top left pixel as a guide
TRIM_COLOR = (255, 255, 255)

# ----------------------------
# Other Defaults
# Arguments will take priority over defaults below
# ----------------------------
# Delete temporary pdf files created during conversion
DELETE = True
# Apply ocrmypdf on output pdf
OCR = False
OCR_LANGUAGES = "eng"
# Reverses ordering of pages
#REVERSE = True
# Logging level
LOG_LEVEL = "WARNING"

# If no title argument given, the default will be the basename of the output path
TITLE = None
AUTHOR = None
