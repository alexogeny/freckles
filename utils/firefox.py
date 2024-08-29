import json
import os
import subprocess
from time import time

from utils.web import download_file

EXTENSIONS_TO_INSTALL = {
    "1password-x-password-manager": "1Password – Password Manager",
    "ublock-origin": "uBlock Origin",
    "decentraleyes": "Decentraleyes",
    "vimium-ff": "Vimium",
}


# https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/addon-ublock-origin-latest.xpi
def get_firefox_version():
    try:
        result = subprocess.run(
            ["firefox", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        version_output = result.stdout.decode().strip()
        version = version_output.split("Mozilla Firefox ")[1]
        return version
    except Exception as e:
        print(f"Error checking Firefox version: {e}")
    return None


def upgrade_firefox():
    try:
        subprocess.run(["sudo", "apt", "remove", "-y", "firefox-esr"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "firefox"], check=True)
        print("Firefox upgraded to the latest stable release.")
    except subprocess.CalledProcessError as e:
        print(f"Error upgrading Firefox: {e}")


def find_firefox_profile():
    profile_path = os.path.expanduser("~/.mozilla/firefox/")

    if not os.path.exists(profile_path):
        print(
            "No Firefox profile directory found. Please run Firefox at least once to generate a profile."
        )
        return None

    profile_dirs = [
        d
        for d in os.listdir(profile_path)
        if d.endswith(".default-esr") or d.endswith(".default-release")
    ]

    if not profile_dirs:
        print(
            "No default Firefox profiles found. Please run Firefox at least once to generate a profile."
        )
        return None

    return os.path.join(profile_path, profile_dirs[0])


def wait_for_firefox_profile():
    profile_dir = None
    while not profile_dir:
        profile_dir = find_firefox_profile()
        if profile_dir:
            print(f"Profile found: {profile_dir}")
            break
        print("Didn't find firefox profile. Please run and close firefox...")
        time.sleep(5)

    return profile_dir


def extension_already_installed(extension_data, extension_name):
    for addon in extension_data.get("addons", []):
        if addon.get("defaultLocale", {}).get("name", "") == extension_name:
            print(f"Extension {extension_name} is already installed.")
            return True
    return False


def get_extension_json(profile_dir):
    extensions_file = os.path.join(profile_dir, "extensions.json")

    # Check if the extension is already installed
    if os.path.exists(extensions_file):
        with open(extensions_file, "r") as f:
            extensions_data = json.load(f)
    return extensions_data or {}


def install_firefox_extension(extension_id):
    try:
        url = f"https://addons.mozilla.org/firefox/downloads/latest/{extension_id}/addon-{extension_id}-latest.xpi"
        download_file(url, extension_id + ".xpi")
        subprocess.run(["firefox", extension_id + ".xpi"], check=True)
        print(f"Extension {extension_id} installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing extension {extension_id}: {e}")
