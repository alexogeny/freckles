from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open the current repository in the default browser.")
    parser.add_argument("--remote", default="origin", help="Remote name to inspect (default: origin).")
    parser.add_argument(
        "--print", dest="only_print", action="store_true", help="Print the URL instead of opening the browser."
    )
    return parser.parse_args(argv)


def _run_git(args: list[str]) -> Optional[str]:
    try:
        result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return (result.stdout or "").strip()


def _normalise_remote_url(url: str) -> Optional[str]:
    if not url:
        return None
    if url.startswith("git@"):
        host_path = url[4:]
        if ":" not in host_path:
            return None
        host, path = host_path.split(":", 1)
        return f"https://{host}/{path.rstrip('.git')}"
    if url.startswith("ssh://git@"):
        remainder = url[len("ssh://git@") :]
        if "/" not in remainder:
            return None
        host, path = remainder.split("/", 1)
        return f"https://{host}/{path.rstrip('.git')}"
    if url.startswith("http://") or url.startswith("https://"):
        return url.rstrip(".git")
    return None


def _infer_from_filesystem(path: Path) -> Optional[str]:
    lower_parts = [part.lower() for part in path.parts]
    for provider in ("github", "gitlab"):
        if provider in lower_parts:
            index = lower_parts.index(provider)
            remainder = path.parts[index + 1 :]
            if len(remainder) >= 2:
                owner = remainder[0]
                repo = remainder[1]
                return f"https://{provider}.com/{owner}/{repo}"
    return None


def open_repository_in_browser(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    remote_url = _run_git(["remote", "get-url", args.remote])
    https_url = _normalise_remote_url(remote_url) if remote_url else None

    if https_url is None:
        toplevel = _run_git(["rev-parse", "--show-toplevel"])
        if toplevel:
            https_url = _infer_from_filesystem(Path(toplevel))
        else:
            https_url = _infer_from_filesystem(Path.cwd())

    if https_url is None:
        raise SystemExit("Unable to determine repository URL for the current directory.")

    if args.only_print:
        print(https_url)
        return 0

    try:
        opened = webbrowser.open(https_url, new=2)
    except webbrowser.Error as error:
        raise SystemExit(f"Failed to launch browser: {error}") from error

    if not opened:
        print(f"Unable to automatically launch a browser. Repository URL: {https_url}")
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return open_repository_in_browser(argv)
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
