#!/usr/bin/env python3
"""Git helper utilities exposed through git aliases.

The helpers offer three commands:

``fresh-switch``
    Fetch (unless ``--no-fetch`` is passed), discover the repository's default
    branch when none is specified and reset the local branch to the chosen
    remote state.

``remote-branches``
    List remote branches sorted by the last commit date, highlighting the
    default branch for quick discovery.

``default-branch``
    Print the repository's default branch.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import List, Sequence

from utils.debian import run


class GitError(RuntimeError):
    """Raised when a git command fails or when data cannot be discovered."""


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def _run_git(
    *args: str,
    capture_output: bool = True,
    check: bool = True,
) -> CommandResult:
    result = run(["git", *args])
    if check and result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise GitError(message or "git command failed")
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    return CommandResult(stdout, stderr, result.returncode)


def _default_branch_from_remote_show(remote: str) -> str | None:
    try:
        output = _run_git("remote", "show", remote).stdout
    except GitError:
        return None
    for line in output.splitlines():
        if "HEAD branch" in line:
            branch = line.split(":", 1)[1].strip()
            if branch and branch != "(unknown)":
                return branch
    return None


def get_default_branch(remote: str = "origin") -> str:
    try:
        symbolic = _run_git("symbolic-ref", f"refs/remotes/{remote}/HEAD").stdout
    except GitError:
        symbolic = ""
    if symbolic:
        return symbolic.rsplit("/", 1)[-1]

    branch = _default_branch_from_remote_show(remote)
    if branch:
        return branch

    for candidate in ("main", "master"):
        result = _run_git(
            "show-ref",
            "--verify",
            f"refs/remotes/{remote}/{candidate}",
            check=False,
        )
        if result.returncode == 0:
            return candidate

    raise GitError(
        "Unable to determine the default branch. Use `git fs <branch>` to "
        "specify one explicitly."
    )


def _remote_branches(remote: str) -> List[str]:
    result = _run_git(
        "for-each-ref",
        "--format=%(refname:short)",
        f"refs/remotes/{remote}",
    )
    return [line for line in result.stdout.splitlines() if line and line != f"{remote}/HEAD"]


def ensure_remote_branch_exists(remote: str, branch: str) -> None:
    remote_ref = f"{remote}/{branch}"
    branches = _remote_branches(remote)
    if remote_ref not in branches:
        raise GitError(f"Remote branch '{remote_ref}' was not found.")


def fresh_switch(branch: str | None, remote: str = "origin", fetch: bool = True) -> None:
    if fetch:
        _run_git("fetch", remote, "--prune", capture_output=False)

    target_branch = branch or get_default_branch(remote)
    ensure_remote_branch_exists(remote, target_branch)
    remote_ref = f"{remote}/{target_branch}"

    _run_git("switch", "-C", target_branch, remote_ref, capture_output=False)
    _run_git("reset", "--hard", remote_ref, capture_output=False)
    sys.stdout.write(f"Switched to {target_branch} tracking {remote_ref}\n")


def list_remote_branches(remote: str = "origin", fetch: bool = True, limit: int | None = None) -> None:
    if fetch:
        _run_git("fetch", remote, "--prune", capture_output=False)

    default_branch = get_default_branch(remote)
    branches = _remote_branches(remote)
    # Sort by committer date descending using git to avoid relying on ``branches`` order.
    ordering_output = _run_git(
        "for-each-ref",
        "--sort=-committerdate",
        "--format=%(refname:short)|%(committerdate:relative)|%(authorname)|%(contents:subject)",
        f"refs/remotes/{remote}",
    ).stdout.splitlines()

    details = {
        line.split("|", 1)[0]: line.split("|", 1)[1]
        for line in ordering_output
        if "|" in line
    }

    ordered = [branch for branch in details if branch in branches]
    if limit is not None:
        ordered = ordered[:limit]

    formatted_lines: List[str] = []
    for entry in ordered:
        name = entry.split("/", 1)[-1]
        if name == "HEAD":
            continue
        indicator = "*" if name == default_branch else " "
        rel_date, author, subject = (details[entry].split("|", 2) + [""] * 3)[:3]
        formatted_lines.append(
            f"{indicator} {name:<24} {rel_date:<16} {author:<18} {subject.strip()}"
        )

    if formatted_lines:
        sys.stdout.write("\n".join(formatted_lines) + "\n")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="git-tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fs_parser = subparsers.add_parser("fresh-switch", help="reset to a remote branch")
    fs_parser.add_argument("branch", nargs="?", help="branch to switch to; defaults to the remote's HEAD")
    fs_parser.add_argument("--remote", default="origin", help="remote name (default: origin)")
    fs_parser.add_argument("--no-fetch", action="store_true", help="do not fetch before switching")

    rb_parser = subparsers.add_parser("remote-branches", help="list remote branches")
    rb_parser.add_argument("--remote", default="origin", help="remote name (default: origin)")
    rb_parser.add_argument("--no-fetch", action="store_true", help="do not fetch before listing")
    rb_parser.add_argument("--limit", type=int, help="limit the number of branches shown")

    db_parser = subparsers.add_parser("default-branch", help="print the default branch")
    db_parser.add_argument("--remote", default="origin", help="remote name (default: origin)")

    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    try:
        if args.command == "fresh-switch":
            fresh_switch(args.branch, remote=args.remote, fetch=not args.no_fetch)
        elif args.command == "remote-branches":
            list_remote_branches(
                remote=args.remote,
                fetch=not args.no_fetch,
                limit=args.limit,
            )
        elif args.command == "default-branch":
            branch = get_default_branch(remote=args.remote)
            sys.stdout.write(branch + "\n")
        else:
            raise GitError(f"Unknown command: {args.command}")
    except GitError as error:
        sys.stderr.write(str(error).strip() + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
