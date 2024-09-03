import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class DebFile:
    name: str
    direct_link: Optional[str] = None
    search_url: Optional[str] = None
    pattern: Optional[re.Pattern] = None


@dataclass
class DebRepository:
    name: str
    gpg: str
    repository: str
    install_name: Optional[str] = None


def check_if_installed(command) -> bool:
    return run(f"which {command}").returncode == 0


def run(command) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, shell=True)


def install_with_apt(package_list: list[str]) -> subprocess.CompletedProcess[str]:
    return run("sudo apt install " + " ".join(package_list) + " -yqq")


def is_debian_12_bookworm():
    import os

    if os.name != "posix":
        return False

    os_release_path = "/etc/os-release"
    if not os.path.exists(os_release_path):
        return False

    try:
        with open(os_release_path) as f:
            os_info = f.read()

        if "ID=debian" not in os_info:
            return False

        if "VERSION_CODENAME=bookworm" not in os_info:
            return False

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def replace_bookworm_with_trixie():
    sources_list_path = "/etc/apt/sources.list"
    backup_path = "/etc/apt/sources.list.bak"

    if not os.path.exists(sources_list_path):
        print(f"{sources_list_path} does not exist.")
        return False

    try:
        subprocess.run(["sudo", "cp", sources_list_path, backup_path], check=True)
        print(f"Backup of sources.list created at {backup_path}.")
    except Exception as e:
        print(f"Failed to create a backup: {e}")
        return False

    try:
        with open(sources_list_path, "r") as file:
            content = file.read()

        content = content.replace("bookworm", "trixie")

        subprocess.run(
            ["sudo", "tee", sources_list_path],
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
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "full-upgrade", "-y"], check=True)
        print("System successfully updated and upgraded.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running apt commands: {e}")
        return False

    return True
