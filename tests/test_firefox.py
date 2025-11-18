import subprocess
from pathlib import Path

import pytest

from utils import firefox


class _FakeCompletedProcess:
    def __init__(self, stdout: str = "", stderr: str = "") -> None:
        self.returncode = 0
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture(autouse=True)
def _temp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _prepare_download(tmp_path: Path, file_name: str) -> Path:
    destination = tmp_path / file_name
    destination.write_bytes(b"addon-bytes")
    return destination


def test_apply_user_chrome_writes_template(tmp_path):
    profile_dir = tmp_path / "profile.default"
    template = tmp_path / "userChrome.css"
    template.write_text("/* css */")

    firefox.USER_CHROME_TEMPLATE = template.as_posix()

    firefox.apply_firefox_user_chrome(profile_dir.as_posix())

    written = profile_dir / "chrome" / "userChrome.css"
    assert written.exists()
    assert written.read_text() == "/* css */"


def test_install_firefox_extension_uses_headless_mode(monkeypatch, tmp_path):
    calls = []

    def fake_download(url, file_name, **_):
        assert url.endswith("latest.xpi")
        return _prepare_download(tmp_path, file_name)

    profile_dir = tmp_path / "profile.default"
    profile_dir.mkdir()

    def fake_find_profile():
        return profile_dir.as_posix()

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return _FakeCompletedProcess(stdout="ok")

    monkeypatch.setattr(firefox, "download_file", fake_download)
    monkeypatch.setattr(firefox, "find_firefox_profile", fake_find_profile)
    monkeypatch.setattr(firefox.subprocess, "run", fake_run)

    result = firefox.install_firefox_extension("ublock-origin")

    assert result is True
    assert not (tmp_path / "ublock-origin.xpi").exists()
    assert calls, "Expected Firefox to be invoked in headless mode"
    command, kwargs = calls[0]
    assert command[:4] == ["firefox", "--headless", "--no-remote", "--profile"]
    assert command[4] == profile_dir.as_posix()
    assert command[5] == "--install-addon"
    assert command[6] == (tmp_path / "ublock-origin.xpi").as_posix()
    assert kwargs["check"] is True
    assert kwargs["stdout"] is subprocess.PIPE
    assert kwargs["stderr"] is subprocess.PIPE
    assert kwargs["text"] is True


def test_install_firefox_extension_logs_failure(monkeypatch, tmp_path, capsys):
    def fake_download(url, file_name, **_):
        return _prepare_download(tmp_path, file_name)

    profile_dir = tmp_path / "profile.default"
    profile_dir.mkdir()

    monkeypatch.setattr(firefox, "download_file", fake_download)
    monkeypatch.setattr(firefox, "find_firefox_profile", lambda: profile_dir.as_posix())

    def fake_run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="boom")

    monkeypatch.setattr(firefox.subprocess, "run", fake_run)

    result = firefox.install_firefox_extension("vimium-ff")

    assert result is False
    assert not (tmp_path / "vimium-ff.xpi").exists()
    captured = capsys.readouterr()
    assert "Error installing extension vimium-ff: boom" in captured.out


def test_install_firefox_extension_without_profile(monkeypatch, tmp_path, capsys):
    def fake_download(url, file_name, **_):
        return _prepare_download(tmp_path, file_name)

    monkeypatch.setattr(firefox, "download_file", fake_download)
    monkeypatch.setattr(firefox, "find_firefox_profile", lambda: None)

    def fail_run(*_args, **_kwargs):
        raise AssertionError("Firefox should not be invoked when no profile exists")

    monkeypatch.setattr(firefox.subprocess, "run", fail_run)

    result = firefox.install_firefox_extension("decentraleyes")

    assert result is False
    assert not (tmp_path / "decentraleyes.xpi").exists()
    captured = capsys.readouterr()
    assert "Firefox profile not found" in captured.out
