import logging

# Define colours that align with the Freckles terminal theme.
BLUE = "\033[38;2;125;178;255m"
GREEN = "\033[38;2;104;201;129m"
PURPLE = "\033[38;2;194;160;255m"
ORANGE = "\033[38;2;246;202;113m"
GOLD = "\033[38;2;255;210;111m"
RED = "\033[38;2;230;130;130m"
PINK = "\033[38;2;255;166;210m"
RESET = "\033[0m"
GRAY = "\033[38;2;122;132;164m"
NEWLINE = "\n"

# Set up logging with custom formatting
logging.basicConfig(format=f"%(message)s{RESET}", level=logging.DEBUG)
logger = logging.getLogger()


# Custom logging functions
def info(message):
    logger.info(f"\033[1;34mINFO: {message}")


def warning(message):
    logger.warning(f"\033[1;33mWARNING: {message}")


def error(message):
    logger.error(f"\033[1;31mERROR: {message}")


def success(message):
    logger.info(f"\033[1;32mSUCCESS: {message}")
