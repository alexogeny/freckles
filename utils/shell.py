import shutil
from pathlib import Path


def configure_shell():
    source = Path("./shell")
    destination = Path.home() / ".shell"
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if (destination / item.name).exists():
            continue
        if item.is_dir():
            shutil.copytree(item, destination / item.name, dirs_exist_ok=True)
        else:
            shutil.copy(item, destination / item.name)
