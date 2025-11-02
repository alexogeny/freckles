import subprocess
from pathlib import Path
from shutil import rmtree
from textwrap import dedent
from typing import List

from .debian import check_if_installed, is_ubuntu as _is_ubuntu, run
from .firefox import install_regular_firefox, setup_mozilla_repo


def is_ubuntu() -> bool:
    return _is_ubuntu()


def list_snap_packages() -> List[str]:
    try:
        result = subprocess.run(
            ["snap", "list"], capture_output=True, text=True, check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
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


def purge_snapd() -> bool:
    if not is_ubuntu():
        return False

    if not check_if_installed("snap"):
        print("snapd is not installed; skipping removal.")
        return False

    packages = list_snap_packages()
    for package in packages:
        removal = run(f"sudo snap remove --purge {package}")
        if removal.returncode != 0:
            print(f"Failed to remove snap package {package}: {removal.stderr}")

    run("sudo systemctl disable --now snapd.socket snapd.service snapd.seeded.service")
    run("sudo apt-get purge -y snapd")
    run("sudo apt-get autoremove -y")
    subprocess.run(["sudo", "rm", "-rf", "/var/cache/snapd"], check=False)

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
    try:
        subprocess.run(
            ["sudo", "install", "-m", "0755", "-d", preference_path.parent.as_posix()],
            check=True,
        )
        subprocess.run(
            ["sudo", "tee", preference_path.as_posix()],
            input=f"{preference_text}\n".encode("utf-8"),
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Failed to update {preference_path}: {exc}")

    return True


def ensure_firefox_from_apt() -> bool:
    if not is_ubuntu():
        return False

    if check_if_installed("firefox"):
        return False

    setup_mozilla_repo()
    install_regular_firefox()
    return True
