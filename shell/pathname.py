import os
from pathlib import Path

from nailpolish import blue, reset


def truncate_path(path):
    home = Path.home().as_posix()
    expanded_path = os.path.expanduser(path)
    prefix = "/"
    if expanded_path.startswith(home):
        prefix = "~/"
        expanded_path = expanded_path[len(home) :]
    parts = expanded_path.strip("/").split("/")
    if len(parts) > 4:
        parts[2:-2] = [".."]
    return prefix + "/".join(parts)


def path_name():
    current_path = os.getcwd()
    truncated_path = truncate_path(current_path)
    return f"{blue}{truncated_path}{reset}"


if __name__ == "__main__":
    assert truncate_path("~/") == "~/"
    assert (
        truncate_path("~/work/gitlab/evenergi/vemo/vemo-core/src")
        == "~/work/gitlab/../vemo-core/src"
    )

    assert (
        truncate_path("/home/alex/work/gitlab/evenergi/vemo/vemo-core/src")
        == "~/work/gitlab/../vemo-core/src"
    )

    assert truncate_path("/etc/apt/sources") == "/etc/apt/sources"

    print(path_name())
