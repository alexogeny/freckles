import hashlib
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def manage_avatar(github_user_id: str = "6896115"):
    home = Path.home()
    face_path = home / ".face"
    avatar_url = f"https://avatars.githubusercontent.com/u/{github_user_id}?v=4"
    accounts_service_path = Path(f"/var/lib/AccountsService/icons/{os.getlogin()}")

    def get_md5(file_path: Path) -> str:
        return hashlib.md5(file_path.read_bytes()).hexdigest()

    def update_system_avatar():
        subprocess.run(
            ["sudo", "cp", str(face_path), str(accounts_service_path)], check=True
        )
        subprocess.run(
            [
                "sudo",
                "dbus-send",
                "--system",
                "--print-reply",
                "--dest=org.freedesktop.Accounts",
                f"/org/freedesktop/Accounts/User{os.getuid()}",
                "org.freedesktop.Accounts.User.SetIconFile",
                f"string:{accounts_service_path}",
            ],
            check=True,
        )

    try:
        with urllib.request.urlopen(avatar_url) as response:
            face_path.write_bytes(response.read())
        print("Avatar downloaded/updated.")
    except urllib.error.URLError as e:
        print(f"Failed to fetch avatar: {e}")
        return

    try:
        if not accounts_service_path.exists() or get_md5(face_path) != get_md5(
            accounts_service_path
        ):
            update_system_avatar()
            print("System avatar updated.")
        else:
            print("System avatar is up-to-date.")
    except PermissionError:
        print(
            "Permission denied when accessing system avatar. Try running the script with sudo."
        )
