import os
import sys
from pathlib import Path
from subprocess import CompletedProcess

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import one_password


def _mkstemp_factory(tmp_path):
    counter = {"value": 0}

    def fake_mkstemp(prefix: str):
        index = counter["value"]
        counter["value"] += 1
        path = tmp_path / f"{prefix}{index}"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
        return fd, path.as_posix()

    return fake_mkstemp


@pytest.mark.parametrize(
    "concealed",
    [False, True],
)
def test_update_item_fields_uses_supported_cli_syntax(tmp_path, monkeypatch, concealed):
    monkeypatch.setattr(
        one_password, "resolve_item_identifier", lambda vault, item, catalog=None: "item-id"
    )

    commands: list[str] = []

    def fake_run(command: str):
        commands.append(command)
        return CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(one_password, "run", fake_run)
    monkeypatch.setattr(one_password.tempfile, "mkstemp", _mkstemp_factory(tmp_path))

    field = one_password.OnePasswordField(
        section="ssh",
        label="private" if concealed else "public",
        value="example-value",
        concealed=concealed,
    )

    assert one_password.update_item_fields("Vault", "Item", [field]) is True
    assert len(commands) == 1

    command = commands[0]
    expected_path = (tmp_path / f"freckles-op-{0}").as_posix()

    assert command.startswith("op item edit --vault Vault item-id")
    assert "[label]" not in command
    assert "[value]" not in command
    assert "[type]" not in command

    if concealed:
        assert f"ssh.private[concealed]=@{expected_path}" in command
    else:
        assert f"ssh.public=@{expected_path}" in command
