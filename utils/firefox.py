import re
import subprocess


def get_firefox_version():
    try:
        result = subprocess.run(
            ["firefox", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        version_output = result.stdout.decode().strip()
        version_match = re.search(r"Firefox (\d+\.\d+)", version_output)
        if version_match:
            return version_match.group(1)
    except Exception as e:
        print(f"Error checking Firefox version: {e}")
    return None
