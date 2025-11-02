from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable

HOST_CHOICES = ("github", "gitlab")
CONTEXT_CHOICES = ("private", "work")


def _normalise_choice(value: str, choices: Iterable[str], *, label: str) -> str:
    normalised = value.strip().lstrip("-").lower()
    if normalised in choices:
        return normalised
    raise SystemExit(f"Unknown {label} '{value}'. Choose one of: {', '.join(sorted(choices))}.")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clone a repository into the freckles directory layout.")
    parser.add_argument("repository", help="Repository in the form owner/name or a full git URL.")
    parser.add_argument("legacy_host", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("legacy_context", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("--host", choices=HOST_CHOICES, default="github", help="Host alias to use (default: github).")
    parser.add_argument(
        "--context",
        choices=CONTEXT_CHOICES,
        default="private",
        help="Context directory to target (default: private).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Clone the full history instead of a shallow clone.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Depth for shallow clones (default: 1). Ignored when --full is supplied.",
    )
    parser.add_argument("--branch", help="Checkout a specific branch immediately after cloning.")
    parser.add_argument(
        "--into",
        help="Override the destination directory. Defaults to ~/context/host/repository.",
    )
    return parser.parse_args(argv)


def _repository_name(repository: str) -> str:
    name = repository.rstrip("/")
    if name.endswith(".git"):
        name = name[: -4]
    return name.rsplit("/", 1)[-1]


def _build_remote(repository: str, host: str, context: str) -> str:
    if any(repository.startswith(prefix) for prefix in ("git@", "ssh://", "https://", "http://")):
        return repository
    repo_name = repository.rstrip("/")
    if not repo_name.endswith(".git"):
        repo_name += ".git"
    return f"git@{host}.com-{context}:{repo_name}"


def _destination_path(repository: str, *, host: str, context: str, override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    home = Path.home()
    directory = home / context / host / _repository_name(repository)
    return directory


def _run_git(args: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], check=True, cwd=cwd)


def clone_repository(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.legacy_host and args.host == "github":
        args.host = _normalise_choice(args.legacy_host, HOST_CHOICES, label="host")
    if args.legacy_context and args.context == "private":
        args.context = _normalise_choice(args.legacy_context, CONTEXT_CHOICES, label="context")

    destination = _destination_path(args.repository, host=args.host, context=args.context, override=args.into)
    if destination.exists():
        if any(destination.iterdir()):
            raise SystemExit(f"Destination {destination} already exists and is not empty.")
        raise SystemExit(f"Destination {destination} already exists.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    remote = _build_remote(args.repository, args.host, args.context)

    clone_cmd = ["clone", "--quiet"]
    if not args.full:
        depth = max(1, args.depth)
        clone_cmd.extend(["--depth", str(depth)])
    if args.branch:
        clone_cmd.extend(["--branch", args.branch])
    clone_cmd.extend([remote, destination.as_posix()])

    try:
        _run_git(clone_cmd)
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"git clone failed with exit code {error.returncode}.") from error

    config_path = Path.home() / f".{args.context}.{args.host}.gitconfig"
    if config_path.exists():
        try:
            _run_git(["config", "--local", "include.path", config_path.as_posix()], cwd=destination)
        except subprocess.CalledProcessError:
            print(f"Warning: unable to include {config_path} in local git config.", file=sys.stderr)

    print(f"Cloned {args.repository} into {destination}")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return clone_repository(argv)
    except KeyboardInterrupt:
        print("Clone cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
