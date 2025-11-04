import json
import os
import shutil
import subprocess
import time


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firefox")
POLICIES_TEMPLATE = os.path.join(TEMPLATE_DIR, "policies.json")
USER_JS_TEMPLATE = os.path.join(TEMPLATE_DIR, "user.js")


def _read_template(path, label):
    if not os.path.exists(path):
        print(f"Missing Firefox {label} template at {path}. Skipping.")
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def apply_firefox_policies():
    template_contents = _read_template(POLICIES_TEMPLATE, "policies.json")
    if template_contents is None:
        return

    policies_dir = "/etc/firefox/policies"
    policies_path = os.path.join(policies_dir, "policies.json")

    try:
        subprocess.run(["sudo", "install", "-d", "-m", "0755", policies_dir], check=True)
        subprocess.run(
            ["sudo", "tee", policies_path],
            input=template_contents.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            check=True,
        )
        subprocess.run(["sudo", "chmod", "0644", policies_path], check=True)
        print("Applied Firefox enterprise policies template.")
    except subprocess.CalledProcessError as error:
        print(f"Failed to apply Firefox policies: {error}")


def apply_firefox_user_js(profile_dir):
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping user.js provisioning.")
        return

    template_contents = _read_template(USER_JS_TEMPLATE, "user.js")
    if template_contents is None:
        return

    os.makedirs(profile_dir, exist_ok=True)
    destination = os.path.join(profile_dir, "user.js")
    with open(destination, "w", encoding="utf-8") as handle:
        handle.write(template_contents)
    os.chmod(destination, 0o644)
    print(f"Synchronized Firefox user.js template to {destination}.")

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


def is_firefox_esr_installed():
    try:
        result = subprocess.run(["dpkg", "-s", "firefox-esr"], capture_output=True)
        return result.returncode == 0
    except Exception:
        pass
    return False


def purge_firefox_esr():
    try:
        subprocess.run(["sudo", "apt", "purge", "-y", "firefox-esr"], check=True)
        print("Firefox ESR purged.")
    except subprocess.CalledProcessError as e:
        print(f"Error purging Firefox ESR: {e}")


def setup_mozilla_repo():
    keyrings_dir = "/etc/apt/keyrings"
    mozilla_key = f"{keyrings_dir}/packages.mozilla.org.asc"
    mozilla_list = "/etc/apt/sources.list.d/mozilla.list"
    mozilla_pref = "/etc/apt/preferences.d/mozilla"

    os.makedirs(keyrings_dir, mode=0o755, exist_ok=True)

    commands = [
        f"wget -qO- https://packages.mozilla.org/apt/repo-signing-key.gpg | sudo tee {mozilla_key} > /dev/null",
        f'echo "deb [signed-by={mozilla_key}] https://packages.mozilla.org/apt mozilla main" | sudo tee {mozilla_list} > /dev/null',
        f'echo "Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1001" | sudo tee {mozilla_pref} > /dev/null',
        "sudo apt update",
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE)
            print(f"Successfully executed: {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"Error output: {e.stderr.decode()}")


def install_regular_firefox():
    install_command = ["sudo", "apt", "install", "-y", "firefox"]

    try:
        subprocess.run(install_command, check=True, stdout=subprocess.DEVNULL)
        print("Firefox installed.")
        return
    except subprocess.CalledProcessError as e:
        print(f"Error installing Firefox: {e}")

    print("Attempting to repair APT dependencies and retry Firefox installation.")

    try:
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "--fix-broken"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(install_command, check=True, stdout=subprocess.DEVNULL)
        print("Firefox installed after repairing dependencies.")
    except subprocess.CalledProcessError as repair_error:
        print(
            "Failed to repair dependencies for Firefox installation: "
            f"{repair_error}"
        )


def purge_esr_profiles():
    profile_path = os.path.expanduser("~/.mozilla/firefox/")

    profile_dirs = [d for d in os.listdir(profile_path) if d.endswith(".default-esr")]

    for profile_dir in profile_dirs:
        profile_dir_path = os.path.join(profile_path, profile_dir)
        try:
            shutil.rmtree(profile_dir_path)
            print(f"Removed profile directory: {profile_dir_path}")
        except Exception as e:
            print(f"Error removing profile directory: {e}")


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
            return True
    return False


def get_extension_json(profile_dir):
    if profile_dir is None:
        print(
            "Firefox profile directory not provided. Skipping extension data lookup."
        )
        return {}

    extensions_file = os.path.join(profile_dir, "extensions.json")
    extensions_data = {}

    if os.path.exists(extensions_file):
        with open(extensions_file, "r") as f:
            extensions_data = json.load(f)
    return extensions_data


def install_firefox_extension(extension_id):
    url = (
        "https://addons.mozilla.org/firefox/downloads/latest/"
        f"{extension_id}/addon-{extension_id}-latest.xpi"
    )
    xpi_path = None

    try:
        xpi_path = download_file(url, extension_id + ".xpi", overwrite=True)
    except Exception as error:  # pragma: no cover - network failures depend on environment
        print(f"Failed to download extension {extension_id}: {error}")
        return False

    try:
        profile_dir = find_firefox_profile()
        if profile_dir is None:
            print(
                "Unable to install Firefox extension "
                f"{extension_id}: Firefox profile not found."
            )
            return False

        install_command = [
            "firefox",
            "--headless",
            "--no-remote",
            "--profile",
            profile_dir,
            "--install-addon",
            xpi_path.as_posix(),
        ]

        subprocess.run(
            install_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"Extension {extension_id} installed.")
        return True
    except subprocess.CalledProcessError as error:
        error_output = (error.stderr or error.stdout or str(error)).strip()
        print(f"Error installing extension {extension_id}: {error_output}")
        return False
    except Exception as error:
        print(f"Unexpected error installing extension {extension_id}: {error}")
        return False
    finally:
        if xpi_path is not None:
            xpi_path.unlink(missing_ok=True)
