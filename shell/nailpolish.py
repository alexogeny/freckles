import logging

# Define colors using ANSI escape codes
blue = "\033[38;5;45m"
green = "\033[38;5;77m"
purple = "\033[38;5;141m"
orange = "\033[38;5;208m"
red = "\033[38;5;203m"
pink = "\033[38;5;219m"
reset = "\033[0m"

# Set up logging with custom formatting
logging.basicConfig(format=f"%(message)s{reset}", level=logging.DEBUG)
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
