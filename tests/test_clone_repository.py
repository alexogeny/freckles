from __future__ import annotations

import json
import pytest

from shell import clone_repository


@pytest.fixture()
def tmp_home(tmp_path, monkeypatch):
    monkeypatch.setattr(clone_repository.Path, "home", lambda: tmp_path)
    return tmp_path


def test_load_dynamic_choices_without_config(tmp_home):
    hosts, contexts = clone_repository._load_dynamic_choices(home=tmp_home)
    assert hosts == clone_repository.DEFAULT_HOST_CHOICES
    assert contexts == clone_repository.DEFAULT_CONTEXT_CHOICES


def test_load_dynamic_choices_with_accounts(tmp_home):
    config_dir = tmp_home / ".config" / "freckles"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "accounts.json"
    config_path.write_text(
        json.dumps(
            {
                "accounts": [
                    {
                        "scope": "Personal",
                        "provider": "GitHub",
                        "alias": "Private",
                    },
                    {
                        "scope": "Client",
                        "provider": "GitLab",
                    },
                    {
                        "scope": "Work",
                        "provider": "GitLab",
                        "alias": "bf",
                    },
                ]
            }
        )
    )

    hosts, contexts = clone_repository._load_dynamic_choices(home=tmp_home)

    assert hosts == ("github", "gitlab")
    assert contexts == ("bf", "client-gitlab", "private", "work")
