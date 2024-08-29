from pathlib import Path

REPOSITORY_LATEST = "https://raw.githubusercontent.com/alexogeny/freckles/prime/"
HOME = Path.home()
SSH_DIR = HOME / ".ssh"
KNOWN_HOSTS = SSH_DIR / "known_hosts"
SSH_CONFIG = SSH_DIR / "config"
