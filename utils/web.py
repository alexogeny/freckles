import json
import re
import urllib.request
from pathlib import Path
from typing import List, Union

from .debian import DebFile, DebRepository, check_if_installed, install_with_apt, run


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


def install_software_list(software_list: List[Union[DebFile, DebRepository]]):
    for software in software_list:
        if check_if_installed(software.name) is True:
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
            download_file(software.gpg, f"{software.name}.gpg", overwrite=True)
            run("sudo install -m 0755 -d /etc/apt/keyrings")
            keyring_path = Path("/etc/apt/keyrings") / f"{software.name}.gpg"
            run(
                f"sudo gpg --dearmor --yes -o {keyring_path} {software.name}.gpg"
            )
            run(f"sudo chmod 644 {keyring_path}")
            Path(f"{software.name}.gpg").unlink(missing_ok=True)
            repo_line = f"deb [signed-by={keyring_path}] {software.repository}"
            run(
                f'echo "{repo_line}" | sudo tee /etc/apt/sources.list.d/{software.name}.list > /dev/null'
            )
            update_result = run("sudo apt-get update -yqq")
            if update_result.returncode != 0:
                print(
                    f"Failed to update package lists for {software.name}: {update_result.stderr.strip()}"
                )
                continue
            print(f"installing {software.name}")
            install_result = install_with_apt([software.install_name or software.name])
            if install_result.returncode != 0:
                print(
                    f"Failed to install {software.install_name or software.name}: {install_result.stderr.strip()}"
                )
