from pathlib import Path

import pytest

from utils import web


class FakeProcess:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture(autouse=True)
def _reset_directories(tmp_path, monkeypatch):
    keyring_dir = tmp_path / "keyrings"
    sources_dir = tmp_path / "sources"
    monkeypatch.setattr(web, "APT_KEYRING_DIR", keyring_dir)
    monkeypatch.setattr(web, "APT_SOURCES_DIR", sources_dir)
    monkeypatch.chdir(tmp_path)
    return keyring_dir, sources_dir


def _fake_run(commands):
    def _runner(command: str):
        commands.append(command)
        if "gpg --dearmor" in command:
            parts = command.split()
            output_path = Path(parts[parts.index("-o") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("binary-key")
            return FakeProcess()
        if "chmod 644" in command:
            path = Path(command.split()[-1])
            if path.exists():
                path.chmod(0o644)
            return FakeProcess()
        parts = command.split()
        if len(parts) >= 4 and parts[0] == "sudo" and parts[2] == "cat":
            target = Path(parts[3])
            return FakeProcess(stdout=target.read_text() if target.exists() else "")
        return FakeProcess()

    return _runner


def test_configure_repository_is_idempotent(monkeypatch):
    repo = web.DebRepository(
        name="spotify",
        gpg="https://example.com/key.gpg",
        repository="https://repository.spotify.com stable non-free",
        install_name="spotify-client",
        check_name="spotify",
    )

    commands: list[str] = []
    monkeypatch.setattr(web, "run", _fake_run(commands))

    def fake_download(url, file_name, **_):
        Path(file_name).write_text("fake")
        return Path(file_name)

    monkeypatch.setattr(web, "download_file", fake_download)

    web._configure_repository(repo)

    repo_path = web.APT_SOURCES_DIR / "spotify.list"
    contents = repo_path.read_text().strip().splitlines()
    assert len(contents) == 1
    expected = f"deb [signed-by={(web.APT_KEYRING_DIR / 'spotify.gpg').as_posix()}] {repo.repository}"
    assert contents[0] == expected

    first_commands = commands.copy()

    commands.clear()
    web._configure_repository(repo)

    # Subsequent runs should only refresh the keyring without rewriting other state.
    expected_gpg_command = (
        f"gpg --dearmor --yes -o {(web.APT_KEYRING_DIR / 'spotify.gpg').as_posix()} spotify.gpg"
    )
    assert commands, "Expected the repository key to be refreshed on subsequent runs"
    assert commands[0] == expected_gpg_command
    if len(commands) == 2:
        assert commands[1] == f"sudo -n {expected_gpg_command}"
    else:
        assert len(commands) == 1

    # Ensure the first run actually executed the expected operations.
    assert any("gpg --dearmor" in cmd for cmd in first_commands)


def test_configure_repository_sources_format(monkeypatch):
    repo = web.DebRepository(
        name="docker",
        gpg="https://download.docker.com/linux/debian/gpg",
        repository="https://download.docker.com/linux/debian bookworm stable",
        install_name="docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
        sources_entry="\n".join(
            [
                "Types: deb",
                "URIs: https://download.docker.com/linux/debian",
                "Suites: bookworm",
                "Components: stable",
                "Signed-By: {signed_by}",
                "",
            ]
        ),
    )

    commands: list[str] = []
    monkeypatch.setattr(web, "run", _fake_run(commands))

    def fake_download(url, file_name, **_):
        Path(file_name).write_text("fake")
        return Path(file_name)

    monkeypatch.setattr(web, "download_file", fake_download)

    web._configure_repository(repo)

    repo_path = web.APT_SOURCES_DIR / "docker.sources"
    assert repo_path.read_text() == (
        "Types: deb\n"
        "URIs: https://download.docker.com/linux/debian\n"
        "Suites: bookworm\n"
        "Components: stable\n"
        f"Signed-By: {(web.APT_KEYRING_DIR / 'docker.gpg').as_posix()}\n"
    )
