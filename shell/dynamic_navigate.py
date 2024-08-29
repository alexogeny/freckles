import os
import pickle
import sys
from pathlib import Path

CACHE_FILE = os.path.expanduser("~/.cdd_cache.pkl")
EXCLUDE_DIRS = {os.path.expanduser("~/.cache").lower()}


def load_cache():
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)


def update_cache(path, cache):
    """Update cache for the given path."""
    path_lower = str(path).lower()
    if path_lower not in cache and path_lower not in EXCLUDE_DIRS:
        if path.exists() and path.is_dir():
            cache[path_lower] = {
                d.lower(): d for d in os.listdir(path) if (path / d).is_dir()
            }
            save_cache(cache)


def is_sequential_match(part, directory):
    """Check if letters in 'part' appear in sequence in 'directory'."""
    it = iter(directory)
    return all(letter in it for letter in part)


def match_directory(part, matches):
    """Perform matching based on the specified algorithm."""
    # Exact match
    if part in matches:
        return matches[part]

    # First letters match but not full match, with no other matches
    first_letter_matches = [v for k, v in matches.items() if k.startswith(part)]
    if len(first_letter_matches) == 1:
        return first_letter_matches[0]

    # Multiple matches, take the first one
    if len(first_letter_matches) > 1:
        return first_letter_matches[0]

    # Sequential letter match
    sequence_matches = [v for k, v in matches.items() if is_sequential_match(part, k)]
    if len(sequence_matches) == 1:
        return sequence_matches[0]

    raise ValueError(f"No suitable match found for '{part}'")


def best_guess_match(path_parts, start_dir, cache):
    current_dir = start_dir
    for part in path_parts:
        if part == "..":
            current_dir = current_dir.parent
        else:
            part_lower = part.lower()
            current_dir_lower = str(current_dir).lower()
            update_cache(current_dir, cache)
            matches = cache.get(current_dir_lower, {})
            matched_dir = match_directory(part_lower, matches)
            current_dir = current_dir / matched_dir
    return current_dir


def dynamic_navigate(path_arg, cache):
    if path_arg.startswith("/"):
        start_dir = Path("/")
        path_parts = path_arg.strip("/").split("/")
    else:
        start_dir = Path(os.path.expanduser("~"))
        path_parts = path_arg.split("/")

    if path_arg.startswith(".."):
        # Navigate up levels based on the number of dots
        up_levels = path_arg.count("..")
        for _ in range(up_levels):
            start_dir = start_dir.parent
        return start_dir
    else:
        # Navigate using best guess match
        return best_guess_match(path_parts, start_dir, cache)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: cdd <path>")
        sys.exit(1)

    path_arg = sys.argv[1]
    cache = load_cache()

    try:
        target_dir = dynamic_navigate(path_arg, cache)
        print(str(target_dir).strip())  # Ensure single line, no extra spaces
    except ValueError as e:
        print(e)
        sys.exit(1)
