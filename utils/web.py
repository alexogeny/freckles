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


def download_file(url, file_name):
    if not Path(file_name).exists():
        urllib.request.urlretrieve(url, file_name)


def get_and_install_from_download_link(link, command):
    file_name = f"{command}.deb"
    download_file(link, file_name)

    package_info = run(f"dpkg -I {file_name}")
    dependencies = []
    for line in package_info.stdout.split("\n"):
        clean = line.strip()
        if clean.startswith("Depends: "):
            dependencies += clean.split("Depends: ")[-1].split(", ")
        if clean.startswith("Recommends: "):
            dependencies += clean.split("Recommends: ")[-1].split(", ")
    install_with_apt(list(set([d.split()[0] for d in dependencies if d])))
    run(f"sudo dpkg -i {file_name}")

    Path(file_name).unlink()


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
            get_and_install_from_download_link(software.direct_link, software.name)
        elif isinstance(software, DebRepository):
            download_file(software.gpg, f"{software.name}.gpg")
            run(
                f"sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg {software.name}.gpg"
            )
            run(
                f'echo "deb {software.repository}" | sudo tee /etc/apt/sources.list.d/{software.name}.list'
            )
            run("sudo apt update")
            print(f"installing {software.name}")
            install_with_apt([software.install_name or software.name])
