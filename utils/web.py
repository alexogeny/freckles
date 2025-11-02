import json
import re
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import List, Optional, Set, Union

from .debian import (
    DebFile,
    DebRepository,
    check_if_installed,
    install_with_apt,
    is_package_installed,
    run,
)


APT_KEYRING_DIR = Path("/etc/apt/keyrings")
APT_SOURCES_DIR = Path("/etc/apt/sources.list.d")


def _retry_operation(operation, attempts: int, backoff: float):
    last_error: Optional[Exception] = None
    total_attempts = max(1, attempts)
    for attempt in range(1, total_attempts + 1):
        try:
            return operation()
        except Exception as error:  # pragma: no cover - network failures are environment dependent
            last_error = error
            if attempt == total_attempts:
                break
            time.sleep(backoff * attempt)
    assert last_error is not None  # for type checkers
    raise RuntimeError(str(last_error)) from last_error


def get_html_from_url(url, attempts: int = 3, backoff: float = 1.0):
    def _download() -> str:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8")

    return _retry_operation(_download, attempts=attempts, backoff=backoff)


def load_json(data):
    return json.loads(data)


def find_download_link_from_html(html, pattern):
    result = re.search(pattern, html)
    if result:
        return html[result.start() : result.end()]
    return None


def download_file(
    url,
    file_name,
    overwrite: bool = False,
    attempts: int = 3,
    backoff: float = 1.0,
) -> Path:
    destination = Path(file_name)
    if overwrite and destination.exists():
        destination.unlink()
    if destination.exists():
        return destination

    def _retrieve() -> Path:
        urllib.request.urlretrieve(url, destination.as_posix())
        return destination

    return _retry_operation(_retrieve, attempts=attempts, backoff=backoff)


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


def _ensure_directory(path: Path, mode: int) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return
    except PermissionError:
        pass
    _ensure_success(
        run(f"sudo install -m {mode:04o} -d {path}"),
        f"Failed to create directory {path}",
    )


def _read_repository_file(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text()
    except PermissionError:
        result = run(f"sudo cat {path}")
        if result.returncode == 0:
            return result.stdout or ""
    return ""


def _write_repository_file(path: Path, content: str) -> None:
    try:
        path.write_text(content)
        return
    except PermissionError:
        pass

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
        handle.write(content)
        temp_path = Path(handle.name)

    try:
        _ensure_success(
            run(f"sudo install -m 0644 {temp_path} {path}"),
            f"Failed to install repository definition at {path}",
        )
    finally:
        temp_path.unlink(missing_ok=True)


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


def _configure_repository(
    repository: DebRepository, key_url: Optional[str] = None
) -> None:
    source_url = key_url or repository.gpg
    try:
        download_file(source_url, f"{repository.name}.gpg", overwrite=True)
    except Exception as error:
        raise RuntimeError(
            f"Failed to download GPG key for {repository.name}: {error}"
        ) from error
    _ensure_directory(APT_KEYRING_DIR, 0o755)
    keyring_path = APT_KEYRING_DIR / f"{repository.name}.gpg"

    if not keyring_path.exists():
        gpg_command = (
            f"gpg --dearmor --yes -o {keyring_path.as_posix()} {repository.name}.gpg"
        )
        result = run(gpg_command)
        if result.returncode != 0:
            result = run(f"sudo {gpg_command}")
        _ensure_success(
            result,
            f"Failed to install GPG key for {repository.name}",
        )

    try:
        keyring_path.chmod(0o644)
    except PermissionError:
        _ensure_success(
            run(f"sudo chmod 644 {keyring_path.as_posix()}"),
            f"Failed to set permissions on keyring for {repository.name}",
        )
    Path(f"{repository.name}.gpg").unlink(missing_ok=True)
    repo_line = f"deb [signed-by={keyring_path.as_posix()}] {repository.repository}"
    repo_path = APT_SOURCES_DIR / f"{repository.name}.list"
    _ensure_directory(repo_path.parent, 0o755)
    existing = _read_repository_file(repo_path)
    if repo_line.strip() in {line.strip() for line in existing.splitlines() if line.strip()}:
        return
    _write_repository_file(repo_path, f"{repo_line}\n")


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


def refresh_repository_keys(
    software_list: List[Union[DebFile, DebRepository]],
    missing_key_ids: Set[str],
) -> bool:
    """Attempt to refresh repository keys using the provided key identifiers."""

    refreshed = False
    if not missing_key_ids:
        return refreshed

    for software in software_list:
        if not isinstance(software, DebRepository):
            continue
        if not software.gpg_template:
            continue
        for key_id in missing_key_ids:
            try:
                _configure_repository(
                    software,
                    key_url=software.gpg_template.format(key_id=key_id),
                )
                refreshed = True
                break
            except (RuntimeError, KeyError) as error:
                print(error)
    return refreshed


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
