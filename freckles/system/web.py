import re
import time
from typing import Iterable, Set

import requests

from .debian import DebFile, DebRepository, run


def install_software_list(software_list: list[DebFile | DebRepository]) -> None:
    for item in software_list:
        if isinstance(item, DebFile):
            _install_deb_file(item)
        elif isinstance(item, DebRepository):
            _install_from_repository(item)


def _install_deb_file(file: DebFile) -> None:
    if file.check_name and _package_installed(file.check_name):
        return

    url = _resolve_deb_url(file)
    if not url:
        print(f"Failed to resolve download URL for {file.name}.")
        return

    result = run(f"curl -L {url} -o /tmp/{file.name}.deb")
    if result.returncode != 0:
        print(f"Failed to download {file.name}: {result.stderr}")
        return

    install = run(f"sudo apt-get install -y /tmp/{file.name}.deb")
    if install.returncode != 0:
        print(f"Failed to install {file.name}: {install.stderr}")


def _install_from_repository(repo: DebRepository) -> None:
    if repo.check_name and _package_installed(repo.check_name):
        return
    ensure_repositories_configured([repo])
    install = run(f"sudo apt-get install -y {repo.install_name}")
    if install.returncode != 0:
        print(f"Failed to install {repo.name}: {install.stderr}")


def _package_installed(name: str) -> bool:
    if not name:
        return False
    result = run(f"dpkg -s {name}")
    return result.returncode == 0


def _resolve_deb_url(file: DebFile) -> str | None:
    if file.direct_link:
        return file.direct_link
    if not file.search_url or not file.pattern:
        return None
    for _ in range(2):
        try:
            response = requests.get(file.search_url, timeout=10)
            if response.ok:
                match = re.search(file.pattern, response.text)
                if match:
                    return match.group(0)
        except requests.RequestException:
            time.sleep(1)
    return None


def ensure_repositories_configured(repositories: Iterable[DebRepository]) -> bool:
    any_configured = False
    for repo in repositories:
        if not repo.gpg or not repo.repository:
            continue
        key_cmd = f"curl -fsSL {repo.gpg} | sudo gpg --dearmor -o /etc/apt/keyrings/{repo.name}.gpg"
        repo_cmd = (
            f"echo \"deb [signed-by=/etc/apt/keyrings/{repo.name}.gpg] {repo.repository}\" | "
            f"sudo tee /etc/apt/sources.list.d/{repo.name}.list"
        )
        run(key_cmd)
        run(repo_cmd)
        any_configured = True
    return any_configured


def refresh_repository_keys(software_list: list[DebFile | DebRepository], missing_key_ids: Set[str]) -> bool:
    refreshed = False
    for item in software_list:
        if not isinstance(item, DebRepository):
            continue
        key_url = item.gpg_template.format(key_id="{key_id}") if item.gpg_template else item.gpg
        for key_id in missing_key_ids:
            url = key_url.format(key_id=key_id)
            result = run(f"curl -fsSL {url} | sudo gpg --dearmor -o /etc/apt/keyrings/{item.name}-{key_id}.gpg")
            if result.returncode == 0:
                refreshed = True
    return refreshed

