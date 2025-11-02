import os
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from subprocess import CompletedProcess
from typing import Dict, Optional, Pattern

OS_RELEASE_PATH = Path("/etc/os-release")


@dataclass
class DebFile:
    name: str
    direct_link: Optional[str] = None
    search_url: Optional[str] = None
    pattern: Optional[Pattern[str]] = None


@dataclass
class DebRepository:
    name: str
    gpg: str
    repository: str
    install_name: Optional[str] = None


def run(command: str) -> subprocess.CompletedProcess[str]:
    """Execute ``command`` via ``subprocess.run`` with output capture enabled."""

    return subprocess.run(command, capture_output=True, text=True, shell=True)


def check_if_installed(command: str) -> bool:
    """Return ``True`` when ``command`` is discoverable on ``$PATH``."""

    result = run(f"which {command}")
    return result.returncode == 0


def install_with_apt(package_list: list[str]) -> CompletedProcess[str]:
    """Install the provided packages using ``apt-get``.

    ``apt`` warns against being used in automation. ``apt-get`` is better suited for
    unattended execution and works consistently across Debian and Ubuntu
    derivatives. Empty package lists are ignored to avoid invoking the package
    manager with no targets.
    """

    packages = [pkg for pkg in package_list if pkg]
    if not packages:
        return CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    command = "sudo apt-get install -yqq " + " ".join(packages)
    result = run(command)

    if result.returncode == 0:
        return result

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    if "unmet dependencies" not in combined_output and "dependency problems" not in combined_output:
        return result

    heal_result = run("sudo apt-get install -f -yqq")
    if heal_result.returncode != 0:
        return result

    return run(command)


def purge_unwanted_packages(
    package_list: list[str],
) -> subprocess.CompletedProcess[str]:
    packages = [pkg for pkg in package_list if pkg]
    if not packages:
        return CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    run("sudo apt-get purge " + " ".join(packages) + " -y")
    run("sudo apt-get autoremove -y")
    return run("sudo apt-get autoclean")


@lru_cache(maxsize=1)
def get_os_release() -> Dict[str, str]:
    """Parse ``/etc/os-release`` once and cache the resulting mapping."""

    if os.name != "posix" or not OS_RELEASE_PATH.exists():
        return {}

    data: Dict[str, str] = {}
    with OS_RELEASE_PATH.open() as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key] = value.strip().strip('"')
    return data


def get_os_release_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience wrapper to fetch a value from ``/etc/os-release``."""

    return get_os_release().get(key, default)


def is_debian_like() -> bool:
    """Return ``True`` for Debian and Debian-derived distributions."""

    os_id = get_os_release_value("ID", "") or ""
    if os_id in {"debian", "ubuntu"}:
        return True
    id_like = get_os_release_value("ID_LIKE", "") or ""
    return any(part == "debian" for part in id_like.split())


def is_debian() -> bool:
    return get_os_release_value("ID") == "debian"


def is_ubuntu() -> bool:
    return get_os_release_value("ID") == "ubuntu"


def get_version_codename(default: Optional[str] = None) -> Optional[str]:
    return get_os_release_value("VERSION_CODENAME", default)


def is_debian_12_bookworm():
    return is_debian() and get_version_codename() == "bookworm"


def replace_bookworm_with_trixie():
    sources_list_path = Path("/etc/apt/sources.list")
    backup_path = Path("/etc/apt/sources.list.bak")

    if not sources_list_path.exists():
        print(f"{sources_list_path} does not exist.")
        return False

    try:
        subprocess.run(["sudo", "cp", sources_list_path.as_posix(), backup_path.as_posix()], check=True)
        print(f"Backup of sources.list created at {backup_path}.")
    except Exception as e:
        print(f"Failed to create a backup: {e}")
        return False

    try:
        with sources_list_path.open("r", encoding="utf-8") as file:
            content = file.read()

        content = content.replace("bookworm", "trixie")

        subprocess.run(
            ["sudo", "tee", sources_list_path.as_posix()],
            input=content.encode("utf-8"),
            check=True,
        )

        print(f"Replaced 'bookworm' with 'trixie' in {sources_list_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to modify {sources_list_path}: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    return True


def run_apt_update_and_upgrade():
    try:
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "full-upgrade", "-y"], check=True)
        print("System successfully updated and upgraded.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running apt commands: {e}")
        return False

    return True
