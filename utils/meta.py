from pathlib import Path

REPOSITORY_LATEST = "https://raw.githubusercontent.com/alexogeny/freckles/prime/"
HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "freckles"
GIT_ACCOUNT_CONFIG_PATH = CONFIG_DIR / "accounts.json"
GIT_ACCOUNTS_DIR = CONFIG_DIR / "git"
SSH_DIR = HOME / ".ssh"
KNOWN_HOSTS = SSH_DIR / "known_hosts"
SSH_CONFIG = SSH_DIR / "config"
