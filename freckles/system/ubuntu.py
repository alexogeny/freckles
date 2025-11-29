import shlex
from pathlib import Path
from shutil import rmtree
from textwrap import dedent
from typing import List, Tuple

from .debian import check_if_installed, is_ubuntu as _is_ubuntu, run
from freckles.firefox.install import install_regular_firefox, setup_mozilla_repo


def is_ubuntu() -> bool:
    return _is_ubuntu()


def list_snap_packages() -> List[str]:
    result = run(["snap", "list"])
    if result.returncode != 0:
        return []

    lines = result.stdout.strip().splitlines()
    if not lines:
        return []

    packages: List[str] = []
    for line in lines[1:]:
        parts = line.split()
        if not parts:
            continue
        packages.append(parts[0])
    return packages


def _snap_priority(package: str) -> Tuple[int, str]:
    """Return a sort key that removes dependent snaps before their bases."""

    name = package.lower()

    if name == "snapd":
        return (4, name)
    if name == "gtk-common-themes":
        return (3, name)
    if name.startswith(("core", "bare")):
        return (2, name)
    if name.startswith("gnome-") or name in {"snapd-desktop-integration"}:
        return (1, name)
    return (0, name)


def _prioritize_snap_packages(packages: List[str]) -> List[str]:
    """Sort snaps so application snaps are removed before shared dependencies."""

    return sorted(packages, key=_snap_priority)


def purge_snapd() -> bool:
    if not is_ubuntu():
        return False

    if not check_if_installed("snap"):
        print("snapd is not installed; skipping removal.")
        return False

    attempts = 0
    packages = _prioritize_snap_packages(list_snap_packages())
    while packages and attempts < 3:
        attempts += 1
        for package in packages:
            removal = run(f"sudo snap remove --purge {package}")
            if removal.returncode != 0:
                print(f"Failed to remove snap package {package}: {removal.stderr}")
        packages = _prioritize_snap_packages(list_snap_packages())

    if packages:
        remaining = ", ".join(packages)
        print(f"Unable to remove snap packages: {remaining}")

    run("sudo systemctl disable --now snapd.socket snapd.service snapd.seeded.service")
    run("sudo apt-get purge -y snapd")
    run("sudo apt-get autoremove -y")
    run(["sudo", "rm", "-rf", "/var/cache/snapd"])

    snap_dir = Path.home() / "snap"
    if snap_dir.exists():
        rmtree(snap_dir, ignore_errors=True)

    preference_text = dedent(
        """
        Package: snapd
        Pin: release a=*
        Pin-Priority: -10
        """
    ).strip()
    preference_path = Path("/etc/apt/preferences.d/nosnap.pref")
    run(["sudo", "install", "-m", "0755", "-d", preference_path.parent.as_posix()])
    update = run(
        f"echo {shlex.quote(preference_text)} | sudo tee {shlex.quote(preference_path.as_posix())}"
    )
    if update.returncode != 0:
        print(f"Failed to update {preference_path}: {update.stderr or update.stdout}")

    return True


def ensure_firefox_from_apt() -> bool:
    if not is_ubuntu():
        return False

    if check_if_installed("firefox"):
        return False

    setup_mozilla_repo()
    install_regular_firefox()
    return True

