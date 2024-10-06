import ctypes
import os
import sys
from pathlib import Path

libc = ctypes.CDLL("libc.so.6")
getcwd = libc.getcwd
getcwd.restype = ctypes.c_char_p

HOME = os.path.expanduser("~")
EXCLUDE_DIRS = {f"{HOME}/.cache".casefold()}


def is_sequential_match(part, directory):
    it = iter(directory)
    return all(letter in it for letter in part)


def match_directory(part, matches):
    part_lower = part.casefold()
    if part_lower in matches:
        return matches[part_lower]
    first_letter_matches = [v for k, v in matches.items() if k.startswith(part_lower)]
    if len(first_letter_matches) == 1:
        return first_letter_matches[0]
    if first_letter_matches:
        return first_letter_matches[0]
    sequence_matches = [
        v for k, v in matches.items() if is_sequential_match(part_lower, k)
    ]
    if len(sequence_matches) == 1:
        return sequence_matches[0]
    raise ValueError(f"No suitable match found for '{part}'")


def get_subdirectories(path):
    try:
        return {d.name.casefold(): d.name for d in os.scandir(path) if d.is_dir()}
    except PermissionError:
        return {}


def best_guess_match(path_parts, start_dir):
    current_dir = start_dir
    for part in path_parts:
        if part == "..":
            current_dir = current_dir.parent
        else:
            current_dir_lower = str(current_dir).casefold()
            if current_dir_lower not in EXCLUDE_DIRS:
                matches = get_subdirectories(current_dir)
                matched_dir = match_directory(part, matches)
                current_dir = current_dir / matched_dir
    return current_dir


def dynamic_navigate(path_arg):
    if path_arg.startswith("/"):
        start_dir = Path("/")
        path_parts = path_arg.strip("/").split("/")
    elif path_arg.strip():
        start_dir = Path(HOME)
        path_parts = path_arg.split("/")
    else:
        return os.path.expanduser("~")

    if path_arg.startswith(".."):
        up_levels = path_arg.count("..")
        for _ in range(up_levels):
            start_dir = start_dir.parent
        return start_dir
    else:
        return best_guess_match(path_parts, start_dir)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: cdd <path>")
        sys.exit(1)

    path_arg = sys.argv[1]

    try:
        target_dir = dynamic_navigate(path_arg)
        print(str(target_dir).strip())
    except ValueError as e:
        print(e)
        sys.exit(1)
