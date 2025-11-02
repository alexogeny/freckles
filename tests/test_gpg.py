import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import gpg  # noqa: E402


class FakeProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_discover_secret_key_parses_output(monkeypatch):
    sample = """
sec:u:4096:1:ABCDEF1234567890:0:0:::\n
aaa\n
fpr:::::::::FINGERPRINT1234567890:\n
""".strip()

    def fake_run(command: str):
        assert command.startswith("gpg --list-secret-keys")
        return FakeProcess(returncode=0, stdout=sample)

    monkeypatch.setattr(gpg, "run", fake_run)

    result = gpg.discover_secret_key("example@example.com")
    assert result == ("ABCDEF1234567890", "FINGERPRINT1234567890")


def test_export_gpg_material_returns_material(monkeypatch):
    public_called = []
    private_called = []
    fingerprint_called = []

    def fake_run(command: str):
        if command.startswith("gpg --armor --export ") and "--export-secret-keys" not in command:
            public_called.append(command)
            return FakeProcess(stdout="PUBLIC-KEY\n")
        if command.startswith("gpg --armor --export-secret-keys"):
            private_called.append(command)
            return FakeProcess(stdout="PRIVATE-KEY\n")
        if command.startswith("gpg --with-colons --fingerprint"):
            fingerprint_called.append(command)
            payload = (
                "sec:u:4096:1:ABCDEF1234567890:0:0:::\n"
                "fpr:::::::::FINGERPRINT1234567890:\n"
            )
            return FakeProcess(stdout=payload)
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(gpg, "run", fake_run)

    material = gpg.export_gpg_material("ABCDEF1234567890")
    assert material is not None
    assert material.key_id == "ABCDEF1234567890"
    assert material.public_key == "PUBLIC-KEY"
    assert material.private_key == "PRIVATE-KEY"
    assert material.fingerprint == "FINGERPRINT1234567890"
    assert public_called and private_called and fingerprint_called


def test_export_gpg_material_handles_failure(monkeypatch):
    def fake_run(command: str):
        return FakeProcess(returncode=1, stderr="boom")

    monkeypatch.setattr(gpg, "run", fake_run)

    material = gpg.export_gpg_material("ABCDEF1234567890")
    assert material is None
