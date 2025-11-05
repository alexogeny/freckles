from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from json import JSONDecodeError
from pathlib import Path
from typing import Iterable, Sequence, Tuple

DEFAULT_HOST_CHOICES: Tuple[str, ...] = ("github", "gitlab")
DEFAULT_CONTEXT_CHOICES: Tuple[str, ...] = ("private", "work")
CONFIG_RELATIVE_PATH = Path(".config") / "freckles" / "accounts.json"


def _normalise_choice(value: str, choices: Iterable[str], *, label: str) -> str:
    normalised = value.strip().lstrip("-").lower()
    if normalised in choices:
        return normalised
    raise SystemExit(f"Unknown {label} '{value}'. Choose one of: {', '.join(sorted(choices))}.")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug


def _account_config_path(home: Path | None = None) -> Path:
    base = home if home is not None else Path.home()
    return base / CONFIG_RELATIVE_PATH


def _load_dynamic_choices(*, home: Path | None = None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    hosts = set(DEFAULT_HOST_CHOICES)
    contexts = set(DEFAULT_CONTEXT_CHOICES)

    config_path = _account_config_path(home)
    try:
        data = json.loads(config_path.read_text())
    except FileNotFoundError:
        return tuple(sorted(hosts)), tuple(sorted(contexts))
    except (OSError, JSONDecodeError, TypeError):
        return tuple(sorted(hosts)), tuple(sorted(contexts))

    accounts = data.get("accounts", [])
    if isinstance(accounts, list):
        for account in accounts:
            if not isinstance(account, dict):
                continue
            provider = account.get("provider")
            if isinstance(provider, str) and provider.strip():
                hosts.add(provider.strip().lower())

            alias = account.get("alias")
            scope = account.get("scope")
            slug = ""
            if isinstance(alias, str) and alias.strip():
                slug = _slugify(alias)
            else:
                slug_parts = []
                if isinstance(scope, str) and scope.strip():
                    slug_parts.append(scope)
                if isinstance(provider, str) and provider.strip():
                    slug_parts.append(provider)
                if slug_parts:
                    slug = _slugify("-".join(slug_parts))
            if slug:
                contexts.add(slug)

    return tuple(sorted(hosts)), tuple(sorted(contexts))


def _default_choice(preferred: str, choices: Sequence[str]) -> str:
    if preferred in choices:
        return preferred
    return choices[0] if choices else preferred


def _parse_args(
    argv: list[str] | None,
    *,
    host_choices: tuple[str, ...],
    context_choices: tuple[str, ...],
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clone a repository into the freckles directory layout.")
    parser.add_argument("repository", help="Repository in the form owner/name or a full git URL.")
    parser.add_argument("legacy_host", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("legacy_context", nargs="?", help=argparse.SUPPRESS)
    host_default = _default_choice("github", host_choices)
    context_default = _default_choice("private", context_choices)
    parser.add_argument(
        "--host",
        choices=host_choices,
        default=host_default,
        help=f"Host alias to use (default: {host_default}).",
    )
    parser.add_argument(
        "--context",
        choices=context_choices,
        default=context_default,
        help=f"Context directory to target (default: {context_default}).",
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
    args = parser.parse_args(argv)
    args._host_default = host_default
    args._context_default = context_default
    args._host_choices = host_choices
    args._context_choices = context_choices
    return args


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
    host_choices, context_choices = _load_dynamic_choices()
    args = _parse_args(argv, host_choices=host_choices, context_choices=context_choices)

    if args.legacy_host and args.host == args._host_default:
        args.host = _normalise_choice(args.legacy_host, args._host_choices, label="host")
    if args.legacy_context and args.context == args._context_default:
        args.context = _normalise_choice(args.legacy_context, args._context_choices, label="context")

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
