#!/usr/bin/env python3

"""
Prints the current git branch, whether there are uncommitted changes,
and the number of additions and deletions.
"""

import re
import subprocess
import sys

from nailpolish import BLUE, GREEN, RED, RESET


def get_git_branch():
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        return ""


def get_git_status():
    try:
        status = (
            subprocess.check_output(
                ["git", "diff", "--shortstat"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        additions = re.search(r"(\d+) insertion", status)
        deletions = re.search(r"(\d+) deletion", status)
        return (
            int(additions.group(1)) if additions else 0,
            int(deletions.group(1)) if deletions else 0,
        )
    except subprocess.CalledProcessError:
        return 0, 0


def main():
    branch = get_git_branch()
    if not branch:
        sys.exit(0)  # Exit silently if not in a git repository

    additions, deletions = get_git_status()

    output = f"{BLUE}{branch}"

    if additions or deletions:
        output += f"{BLUE}("
        if additions:
            output += f"{GREEN}+{additions}"
        if additions and deletions:
            output += f"{BLUE}/"
        if deletions:
            output += f"{RED}-{deletions}"
        output += f"{BLUE})"

    print(f"{output}{RESET} ")


if __name__ == "__main__":
    main()
