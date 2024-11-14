import logging

# Define colors using ANSI escape codes
BLUE = "\033[38;5;39m"
GREEN = "\033[38;5;76m"
PURPLE = "\033[38;5;99m"
ORANGE = "\033[38;5;208m"
GOLD = "\033[38;5;220m"
RED = "\033[38;5;203m"
PINK = "\033[38;5;206m"
RESET = "\033[0m"
GRAY = "\033[38;5;244m"
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
