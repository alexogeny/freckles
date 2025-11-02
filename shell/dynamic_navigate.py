"""Fuzzy navigation helper used by the ``nn`` shell function.

The previous implementation only understood absolute paths or shortcuts from the
user's home directory.  It now supports ``.``, ``..``, the previous directory
marker (``-``) and tilde expansion while still offering fuzzy matching for each
path segment.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

HOME = Path.home()
EXCLUDE_DIRS = {HOME.joinpath(".cache").as_posix().casefold()}


@dataclass(frozen=True)
class MatchResult:
    """A wrapper that keeps the original directory name and its lower-case key."""

    key: str
    value: str


def _iter_subdirectories(path: Path) -> Iterator[MatchResult]:
    try:
        with os.scandir(path) as iterator:
            for entry in iterator:
                if entry.is_dir():
                    yield MatchResult(entry.name.casefold(), entry.name)
    except PermissionError:
        return


def _is_sequential_match(part: str, directory: str) -> bool:
    it = iter(directory)
    return all(letter in it for letter in part)


def _match_directory(part: str, matches: Dict[str, str]) -> str:
    part_lower = part.casefold()
    if part_lower in matches:
        return matches[part_lower]

    first_letter_matches = [v for k, v in matches.items() if k.startswith(part_lower)]
    if len(first_letter_matches) == 1:
        return first_letter_matches[0]
    if first_letter_matches:
        # Fall back to the first prefix match for deterministic behaviour.
        return sorted(first_letter_matches)[0]

    sequence_matches = [
        v for k, v in matches.items() if _is_sequential_match(part_lower, k)
    ]
    if len(sequence_matches) == 1:
        return sequence_matches[0]
    if sequence_matches:
        return sorted(sequence_matches)[0]

    raise ValueError(f"No suitable match found for '{part}'")


def _best_guess_match(path_parts: Iterable[str], start_dir: Path) -> Path:
    current_dir = start_dir
    for part in path_parts:
        if part in {"", "."}:
            continue
        if part == "..":
            current_dir = current_dir.parent
            continue

        current_dir_lower = current_dir.as_posix().casefold()
        if current_dir_lower in EXCLUDE_DIRS:
            continue

        matches = {match.key: match.value for match in _iter_subdirectories(current_dir)}
        matched_dir = _match_directory(part, matches)
        current_dir = current_dir / matched_dir
    return current_dir


def _split_path_parts(path_arg: str) -> List[str]:
    expanded = os.path.expanduser(path_arg)
    if expanded.startswith("/"):
        # ``Path.parts`` keeps the leading slash as its own element so we strip it.
        return [part for part in Path(expanded).parts if part not in {"/", ""}]
    return [part for part in expanded.split("/")]


def dynamic_navigate(path_arg: str) -> Path:
    if not path_arg or not path_arg.strip():
        return HOME

    trimmed = path_arg.strip()
    if trimmed == "-":
        oldpwd = os.environ.get("OLDPWD")
        return Path(oldpwd) if oldpwd else Path.cwd()

    expanded = os.path.expanduser(trimmed)
    if expanded.startswith("/"):
        start_dir = Path("/")
    elif trimmed.startswith("./") or trimmed.startswith("../") or trimmed == ".":
        start_dir = Path.cwd()
    else:
        start_dir = HOME

    parts = _split_path_parts(trimmed)
    return _best_guess_match(parts, start_dir)


def _main(argv: List[str]) -> int:
    if len(argv) > 1 and argv[1] in {"-h", "--help"}:
        print("Usage: nn [path]")
        return 0

    if len(argv) == 1:
        target = ""
    else:
        target = " ".join(argv[1:])

    try:
        target_dir = dynamic_navigate(target)
    except ValueError as error:
        print(error)
        return 1

    print(str(target_dir).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
