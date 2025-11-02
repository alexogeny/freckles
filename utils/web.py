import json
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import List, Optional, Union

from .debian import (
    DebFile,
    DebRepository,
    check_if_installed,
    install_with_apt,
    is_package_installed,
    run,
)


def get_html_from_url(url):
    response = urllib.request.urlopen(url)
    html = response.read().decode("utf-8")
    return html


def load_json(data):
    return json.loads(data)


def find_download_link_from_html(html, pattern):
    result = re.search(pattern, html)
    if result:
        return html[result.start() : result.end()]
    return None


def download_file(url, file_name, overwrite: bool = False) -> Path:
    destination = Path(file_name)
    if overwrite and destination.exists():
        destination.unlink()
    if not destination.exists():
        urllib.request.urlretrieve(url, destination.as_posix())
    return destination


def _ensure_success(result: subprocess.CompletedProcess[str], context: str) -> None:
    if result.returncode == 0:
        return
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    message = stderr or stdout or "unknown error"
    raise RuntimeError(f"{context}: {message}")


def _software_is_installed(command_name: Optional[str], package_name: Optional[str]) -> bool:
    if command_name and check_if_installed(command_name):
        return True
    if package_name and is_package_installed(package_name):
        return True
    return False


def get_and_install_from_download_link(link, command):
    if not link:
        raise ValueError(f"Unable to determine a download link for {command}")

    file_name = Path(f"{command}.deb")
    download_file(link, file_name, overwrite=True)

    package_info = run(f"dpkg -I {file_name}")
    dependencies = []
    for line in package_info.stdout.split("\n"):
        clean = line.strip()
        if clean.startswith("Depends: "):
            dependencies += clean.split("Depends: ")[-1].split(", ")
        if clean.startswith("Recommends: "):
            dependencies += clean.split("Recommends: ")[-1].split(", ")

    dependency_names = sorted({d.split()[0] for d in dependencies if d})
    if dependency_names:
        install_with_apt(dependency_names)

    install_result = run(f"sudo dpkg -i {file_name}")
    if install_result.returncode != 0:
        print(
            f"Initial install of {command} failed; attempting to resolve missing dependencies."
        )
        heal_result = run("sudo apt-get install -f -yqq")
        if heal_result.returncode == 0:
            install_result = run(f"sudo dpkg -i {file_name}")
        else:
            print(
                f"Unable to repair dependency issues for {command}: {heal_result.stderr.strip()}"
            )

    if install_result.returncode != 0:
        print(install_result.stderr.strip())
        raise RuntimeError(f"Failed to install {command}; see logs above for details.")

    file_name.unlink(missing_ok=True)


def _configure_repository(repository: DebRepository) -> None:
    download_file(repository.gpg, f"{repository.name}.gpg", overwrite=True)
    _ensure_success(
        run("sudo install -m 0755 -d /etc/apt/keyrings"),
        f"Failed to create keyring directory for {repository.name}",
    )
    keyring_path = Path("/etc/apt/keyrings") / f"{repository.name}.gpg"
    _ensure_success(
        run(f"sudo gpg --dearmor --yes -o {keyring_path} {repository.name}.gpg"),
        f"Failed to install GPG key for {repository.name}",
    )
    _ensure_success(
        run(f"sudo chmod 644 {keyring_path}"),
        f"Failed to set permissions on keyring for {repository.name}",
    )
    Path(f"{repository.name}.gpg").unlink(missing_ok=True)
    repo_line = f"deb [signed-by={keyring_path}] {repository.repository}"
    _ensure_success(
        run(
            f'echo "{repo_line}" | '
            f"sudo tee /etc/apt/sources.list.d/{repository.name}.list > /dev/null"
        ),
        f"Failed to configure repository for {repository.name}",
    )


def ensure_repositories_configured(
    software_list: List[Union[DebFile, DebRepository]]
) -> bool:
    configured = False
    for software in software_list:
        if isinstance(software, DebRepository):
            try:
                _configure_repository(software)
                configured = True
            except RuntimeError as error:
                print(error)
    return configured


def install_software_list(software_list: List[Union[DebFile, DebRepository]]):
    update_result = run("sudo apt-get update -yqq")
    _ensure_success(update_result, "Failed to refresh apt package lists")

    for software in software_list:
        command_name = getattr(software, "check_name", None) or software.name
        package_name = getattr(software, "package_name", None)
        if isinstance(software, DebRepository):
            package_name = package_name or software.install_name or software.name

        if _software_is_installed(command_name, package_name):
            continue
        if isinstance(software, DebFile):
            if software.search_url and not software.direct_link:
                print(f"Getting download link for {software.name}")
                html = get_html_from_url(software.search_url)
                software.direct_link = find_download_link_from_html(
                    html, software.pattern
                )
            if not software.direct_link:
                print(
                    f"Skipping {software.name}; unable to determine a download link."
                )
                continue
            get_and_install_from_download_link(software.direct_link, software.name)
        elif isinstance(software, DebRepository):
            _configure_repository(software)
            update_result = run("sudo apt-get update -yqq")
            _ensure_success(update_result, f"Failed to update apt cache for {software.name}")
            print(f"installing {software.name}")
            install_result = install_with_apt([software.install_name or software.name])
            _ensure_success(
                install_result,
                f"Failed to install {software.install_name or software.name}",
            )

        if not _software_is_installed(command_name, package_name):
            raise RuntimeError(
                f"{software.name} installation completed but the software was not detected."
            )
