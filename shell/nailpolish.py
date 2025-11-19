import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """ANSI escape palette used throughout Freckles."""

    blue: str = "\033[38;2;125;178;255m"
    green: str = "\033[38;2;104;201;129m"
    purple: str = "\033[38;2;194;160;255m"
    orange: str = "\033[38;2;246;202;113m"
    gold: str = "\033[38;2;255;210;111m"
    red: str = "\033[38;2;230;130;130m"
    pink: str = "\033[38;2;255;166;210m"
    gray: str = "\033[38;2;122;132;164m"
    reset: str = "\033[0m"
    dim: str = "\033[2m"
    normal: str = "\033[22m"
    bright: str = "\033[1m"


DEFAULT_PALETTE = Palette()

# Preserve legacy constant names for compatibility.
BLUE = DEFAULT_PALETTE.blue
GREEN = DEFAULT_PALETTE.green
PURPLE = DEFAULT_PALETTE.purple
ORANGE = DEFAULT_PALETTE.orange
GOLD = DEFAULT_PALETTE.gold
RED = DEFAULT_PALETTE.red
PINK = DEFAULT_PALETTE.pink
GRAY = DEFAULT_PALETTE.gray
RESET = DEFAULT_PALETTE.reset
DIM = DEFAULT_PALETTE.dim
NORMAL = DEFAULT_PALETTE.normal
BRIGHT = DEFAULT_PALETTE.bright
NEWLINE = "\n"


# Set up logging with custom formatting
logging.basicConfig(format=f"%(message)s{RESET}", level=logging.DEBUG)
logger = logging.getLogger()


def info(message):
    logger.info(f"{BRIGHT}{BLUE}INFO:{RESET} {message}")


def warning(message):
    logger.warning(f"{BRIGHT}{ORANGE}WARNING:{RESET} {message}")


def error(message):
    logger.error(f"{BRIGHT}{RED}ERROR:{RESET} {message}")


def success(message):
    logger.info(f"{BRIGHT}{GREEN}SUCCESS:{RESET} {message}")
