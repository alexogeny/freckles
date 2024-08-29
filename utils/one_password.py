import time

from .debian import run


def ensure_op_connected():
    while run("op account list").stdout == "":
        print("Waiting for connection between op CLI and desktop app...")
        time.sleep(5)
