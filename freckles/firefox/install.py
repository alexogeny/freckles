from __future__ import annotations

import os
import shutil

from freckles.system.debian import run


def get_firefox_version():
    result = run(["firefox", "--version"])
    if result.returncode != 0:
        print(f"Error checking Firefox version: {result.stderr or result.stdout}")
        return None
    version_output = (result.stdout or "").strip()
    if "Mozilla Firefox " not in version_output:
        return None
    return version_output.split("Mozilla Firefox ")[1]


def is_firefox_esr_installed():
    result = run(["dpkg", "-s", "firefox-esr"])
    return result.returncode == 0


def purge_firefox_esr():
    result = run(["sudo", "apt", "purge", "-y", "firefox-esr"])
    if result.returncode != 0:
        print(f"Error purging Firefox ESR: {result.stderr or result.stdout}")
        return
    print("Firefox ESR purged.")


def setup_mozilla_repo():
    keyrings_dir = "/etc/apt/keyrings"
    mozilla_key = f"{keyrings_dir}/packages.mozilla.org.asc"
    mozilla_list = "/etc/apt/sources.list.d/mozilla.list"
    mozilla_pref = "/etc/apt/preferences.d/mozilla"

    os.makedirs(keyrings_dir, mode=0o755, exist_ok=True)

    commands = [
        f"wget -qO- https://packages.mozilla.org/apt/repo-signing-key.gpg | sudo tee {mozilla_key} > /dev/null",
        f'echo "deb [signed-by={mozilla_key}] https://packages.mozilla.org/apt mozilla main" | sudo tee {mozilla_list} > /dev/null',
        f'echo "Package: *\\nPin: origin packages.mozilla.org\\nPin-Priority: 1001" | sudo tee {mozilla_pref} > /dev/null',
        "sudo apt update",
    ]

    for cmd in commands:
        result = run(cmd)
        if result.returncode != 0:
            print(f"Failed to execute: {cmd}: {result.stderr or result.stdout}")
        else:
            print(f"Successfully executed: {cmd}")


def install_regular_firefox():
    install_command = ["sudo", "apt", "install", "-y", "firefox"]

    result = run(install_command)
    if result.returncode == 0:
        print("Firefox installed.")
        return

    print("Attempting to repair APT dependencies and retry Firefox installation.")
    repair = run(["sudo", "apt-get", "install", "-y", "--fix-broken"])
    if repair.returncode != 0:
        print("Failed to repair dependencies for Firefox installation.")
        return
    retry = run(install_command)
    if retry.returncode == 0:
        print("Firefox installed after repairing dependencies.")
    else:
        print("Failed to install Firefox after repairing dependencies.")


def purge_esr_profiles():
    profile_path = os.path.expanduser("~/.mozilla/firefox/")

    if not os.path.exists(profile_path):
        return

    profile_dirs = [d for d in os.listdir(profile_path) if d.endswith(".default-esr")]

    for profile_dir in profile_dirs:
        profile_dir_path = os.path.join(profile_path, profile_dir)
        try:
            shutil.rmtree(profile_dir_path)
            print(f"Removed profile directory: {profile_dir_path}")
        except Exception as e:
            print(f"Error removing profile directory: {e}")
