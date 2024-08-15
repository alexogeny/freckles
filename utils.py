import json
import re
import subprocess
import textwrap
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union, Literal
REPOSITORY_LATEST = "https://raw.githubusercontent.com/alexogeny/freckles/prime/"

@dataclass
class DebFile:
    name: str
    direct_link: Optional[str] = None
    search_url: Optional[str] = None
    pattern: Optional[re.Pattern] = None


@dataclass
class DebRepository:
    name: str
    gpg: str
    repository: str
    install_name: Optional[str] = None


def run(command) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, shell=True)


def check_if_installed(command) -> bool:
    return run(f"which {command}").returncode == 0


def install_with_apt(package_list: list[str]) -> subprocess.CompletedProcess[str]:
    return run("sudo apt install " + " ".join(package_list) + " -yqq")


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
            print(f"Already installed {software.name}")
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


def configure_vscode():
    vscode = Path.home() / ".config" / "Code" / "User"
    if not vscode.exists():
        vscode.mkdir(parents=True, exist_ok=True)
    settings, keybindings = vscode / "settings.json", vscode / "keybindings.json"
    if not settings.exists():
        download_file(
            REPOSITORY_LATEST + "vscode/settings.link.json",
            "settings.json",
        )
        Path("settings.json").rename(settings)
    if not keybindings.exists():
        download_file(
            REPOSITORY_LATEST + "vscode/keybinds.link.json",
            "keybinds.json",
        )
        Path("keybinds.json").rename(keybindings)


def ensure_op_connected():
    while run("op account list").stdout == "":
        print("Waiting for connection between op CLI and desktop app...")
        time.sleep(5)



HOME = Path.home()
SSH_DIR = HOME / ".ssh"
KNOWN_HOSTS = SSH_DIR / "known_hosts"
SSH_CONFIG = SSH_DIR / "config"
known_hosts_content = textwrap.dedent("""
gitlab.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAfuCHKVTjquxvt6CM6tdG4SLp1Btn/nOeHHE5UOzRdf
gitlab.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsj2bNKTBSpIYDEGk9KxsGh3mySTRgMtXL583qmBpzeQ+jqCMRgBqB98u3z++J1sKlXHWfM9dyhSevkMwSbhoR8XIq/U0tCNyokEi/ueaBMCvbcTHhO7FcwzY92WK4Yt0aGROY5qX2UKSeOvuP4D6TPqKF1onrSzH9bx9XUf2lEdWT/ia1NEKjunUqu1xOB/StKDHMoX4/OKyIzuS0q/T1zOATthvasJFoPrAjkohTyaDUz2LN5JoH839hViyEG82yB+MjcFV5MU3N1l1QL3cVUCh93xSaua1N85qivl+siMkPGbO5xR/En4iEY6K2XPASUEMaieWVNTRCtJ4S8H+9
gitlab.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBFSMqzJeV9rUzU4kWitGjeR4PWSa29SPqJ1fVkhtj3Hw9xjLVXVYrU9QlYWrOLXBpQ6KWjbjTDTdDkoohFzgbEY=

github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=
github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=
""")


def write_known_hosts():
    if not KNOWN_HOSTS.exists():
        KNOWN_HOSTS.write_text(known_hosts_content)


def get_favorite_git_items():
    return [
        i
        for i in run("op item list --favorite").stdout.lower().splitlines()
        if "git" in i
    ]


def setup_ssh_key(vault, git_provider, item_list):
    matching_item = next(
        (i for i in item_list if vault in i and git_provider in i), None
    )
    if matching_item:
        key = SSH_DIR / f"{vault}.{git_provider}"
        op_path = f"op://{vault}/{git_provider}/ssh"
        run(f'op read --force --out-file "{key}.pub" "{op_path}/public"')
        run(f'op read --force --out-file "{key}" "{op_path}/private"')
        if key.name not in run("ssh-add -l").stdout.lower():
            run(f'ssh-add "{key}"')


def add_ssh_config(vault, git):
    suffix = "-work" if vault == "work" else ""
    config_entry = textwrap.dedent(f"""
        Host {git}.com{suffix}
            HostName {git}.com
            AddKeysToAgent yes
            IdentityFile ~/.ssh/{vault}.{git}
            User git
    """)
    existing_config = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    if f"Host {git}.com{suffix}" not in existing_config:
        with SSH_CONFIG.open("a") as fh:
            fh.write(config_entry)


def configure_ssh():
    ensure_op_connected()
    write_known_hosts()

    item_list = get_favorite_git_items()

    for vault in ["private", "work"]:
        for git_provider in ["github", "gitlab"]:
            setup_ssh_key(vault, git_provider, item_list)
            add_ssh_config(vault, git_provider)


def configure_git():
    for filename in [
        ".gitconfig",
        ".gitignore",
        ".personal.gitlab.gitconfig",
        ".personal.github.gitconfig",
    ]:
        local_path = HOME / filename
        if not local_path.exists():
            download_file(
                REPOSITORY_LATEST + "git/" + filename,
                local_path,
            )


def clone_repository(
    repository_path,
    hostname: Literal["github"] | Literal["gitlab"],
    account_type: Literal["private"] | Literal["work"],
):
    local = f"~/{account_type}/{hostname}/{repository_path}"
    if Path(local).exists():
        raise ValueError("Already exists")
    else:
        Path(local).mkdir(parents=True)
    suffix: Literal["-work"] | Literal[""] = "-work" if account_type == "work" else ""
    repository_path = f"git@{hostname}{suffix}:{repository_path}.git"
    git_config = f"~/.{account_type}.{hostname}.gitconfig"
    run(
        f'git --git-dir="{local}.git" --work-tree="{local}" config --local include.path "{git_config}"'
    )


def browser():
    current_directory = str(Path.cwd()).lower()
    url = None
    if "/github/" in current_directory:
        url = "https://github.com/" + current_directory.split("/github/")[-1]
        run(f"xdg-open {url}")
    elif "/gitlab/" in current_directory:
        url = "https://gitlab.com/" + current_directory.split("/gitlab/")[-1]
        run(f"xdg-open {url}")
