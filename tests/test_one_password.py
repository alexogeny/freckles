import json
import os
import shlex
import sys
from pathlib import Path
from subprocess import CompletedProcess

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from freckles.secrets import one_password


def _mkstemp_factory(tmp_path):
    counter = {"value": 0}

    def fake_mkstemp(prefix: str, suffix: str = ""):
        index = counter["value"]
        counter["value"] += 1
        path = tmp_path / f"{prefix}{index}{suffix}"
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
    payloads: list[str] = []

    def fake_run(command: str):
        commands.append(command)
        tokens = shlex.split(command)
        if "--template" in tokens:
            index = tokens.index("--template")
            if index + 1 < len(tokens):
                payload_path = Path(tokens[index + 1])
                payloads.append(payload_path.read_text())
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

    assert command.startswith("op item edit --vault Vault item-id")
    assert "--template" in command

    assert payloads, "expected payload to be captured"
    payload = json.loads(payloads[0])
    assert "fields" in payload and len(payload["fields"]) == 1
    field_payload = payload["fields"][0]
    assert field_payload["label"] == ("private" if concealed else "public")
    assert field_payload["value"] == "example-value"
    assert "@" not in field_payload["value"]
    assert field_payload["type"] == ("concealed" if concealed else "string")
    assert field_payload.get("section", {}).get("id") == "ssh"


def test_update_item_fields_handles_cli_panic(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        one_password, "resolve_item_identifier", lambda vault, item, catalog=None: "item-id"
    )

    commands: list[str] = []

    def fake_run(command: str):
        commands.append(command)
        tokens = shlex.split(command)
        if "--template" in tokens:
            index = tokens.index("--template")
            if index + 1 < len(tokens):
                payload_path = Path(tokens[index + 1])
                payload_path.read_text()
        return CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr="panic: runtime error: invalid memory address or nil pointer dereference",
        )

    monkeypatch.setattr(one_password, "run", fake_run)
    monkeypatch.setattr(one_password.tempfile, "mkstemp", _mkstemp_factory(tmp_path))

    field = one_password.OnePasswordField(
        section="ssh",
        label="public",
        value="example-value",
    )

    assert one_password.update_item_fields("Vault", "Item", [field]) is False
    assert len(commands) == 1

    output = capsys.readouterr().out
    assert "The 1Password CLI encountered an unexpected crash" in output
