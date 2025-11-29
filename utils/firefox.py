import json
import os
import shutil
import time
import shlex

from .debian import run


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firefox")
POLICIES_TEMPLATE = os.path.join(TEMPLATE_DIR, "policies.json")
USER_JS_TEMPLATE = os.path.join(TEMPLATE_DIR, "user.js")
HANDLERS_TEMPLATE = os.path.join(TEMPLATE_DIR, "handlers.json")
CONTAINERS_TEMPLATE = os.path.join(TEMPLATE_DIR, "containers.json")
USER_CHROME_TEMPLATE = os.path.join(TEMPLATE_DIR, "chrome", "userChrome.css")


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

    create_dir = run(["sudo", "install", "-d", "-m", "0755", policies_dir])
    write_policy = run(
        f"echo {shlex.quote(template_contents)} | sudo tee {policies_path}"
    )
    set_perms = run(["sudo", "chmod", "0644", policies_path])
    if any(result.returncode != 0 for result in (create_dir, write_policy, set_perms)):
        print("Failed to apply Firefox policies.")
        return
    print("Applied Firefox enterprise policies template.")


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


def apply_firefox_handlers(profile_dir):
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping handlers.json provisioning.")
        return

    template_contents = _read_template(HANDLERS_TEMPLATE, "handlers.json")
    if template_contents is None:
        return

    os.makedirs(profile_dir, exist_ok=True)
    destination = os.path.join(profile_dir, "handlers.json")
    with open(destination, "w", encoding="utf-8") as handle:
        handle.write(template_contents)
    os.chmod(destination, 0o644)
    print(f"Synchronized Firefox handlers template to {destination}.")


def apply_firefox_containers(profile_dir):
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping containers.json provisioning.")
        return

    template_contents = _read_template(CONTAINERS_TEMPLATE, "containers.json")
    if template_contents is None:
        return

    os.makedirs(profile_dir, exist_ok=True)
    destination = os.path.join(profile_dir, "containers.json")
    with open(destination, "w", encoding="utf-8") as handle:
        handle.write(template_contents)
    os.chmod(destination, 0o644)
    print(f"Synchronized Firefox containers template to {destination}.")


def apply_firefox_user_chrome(profile_dir):
    if profile_dir is None:
        print("Firefox profile directory not provided. Skipping userChrome.css provisioning.")
        return

    template_contents = _read_template(USER_CHROME_TEMPLATE, "userChrome.css")
    if template_contents is None:
        return

    chrome_dir = os.path.join(profile_dir, "chrome")
    os.makedirs(chrome_dir, exist_ok=True)
    destination = os.path.join(chrome_dir, "userChrome.css")
    with open(destination, "w", encoding="utf-8") as handle:
        handle.write(template_contents)
    os.chmod(destination, 0o644)
    print(f"Synchronized Firefox userChrome.css template to {destination}.")

from utils.web import download_file

EXTENSIONS_TO_INSTALL = {
    "1password-x-password-manager": "1Password – Password Manager",
    "ublock-origin": "uBlock Origin",
    "decentraleyes": "Decentraleyes",
    "vimium-ff": "Vimium",
}


# https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/addon-ublock-origin-latest.xpi
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
        f'echo "Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1001" | sudo tee {mozilla_pref} > /dev/null',
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

        result = run(" ".join(install_command))
        if result.returncode == 0:
            print(f"Extension {extension_id} installed.")
            return True
        error_output = (result.stderr or result.stdout or "").strip()
        print(f"Error installing extension {extension_id}: {error_output}")
        return False
    except Exception as error:
        print(f"Unexpected error installing extension {extension_id}: {error}")
        return False
    finally:
        if xpi_path is not None:
            xpi_path.unlink(missing_ok=True)
