import shutil
from pathlib import Path


SHELL_SOURCE_LINE = 'source "$HOME/.shell/aliases.sh"'


def ensure_shell_loader(shell_rc: Path) -> None:
    """Ensure the shell rc file loads the freckles shell configuration."""

    block_header = "# freckles shell configuration"
    block_lines = [
        block_header,
        'if [ -f "$HOME/.shell/aliases.sh" ]; then',
        f"  {SHELL_SOURCE_LINE}",
        "fi",
    ]
    block_text = "\n".join(block_lines) + "\n"

    shell_rc.parent.mkdir(parents=True, exist_ok=True)
    if shell_rc.exists():
        contents = shell_rc.read_text()
    else:
        contents = ""

    if SHELL_SOURCE_LINE in contents:
        return

    with shell_rc.open("a", encoding="utf-8") as handle:
        if contents and not contents.endswith("\n"):
            handle.write("\n")
        if contents:
            handle.write("\n")
        handle.write(block_text)


def configure_shell():
    source = Path("./shell")
    if not source.exists():
        raise FileNotFoundError("Expected ./shell directory to exist next to setup script")

    destination = Path.home() / ".shell"
    destination.mkdir(parents=True, exist_ok=True)

    for item in source.iterdir():
        # Skip Python bytecode or other transient artefacts that may have been
        # generated locally.
        if item.name.endswith(".pyc") or item.name == "__pycache__":
            continue

        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

    ensure_shell_loader(Path.home() / ".bashrc")
    ensure_shell_loader(Path.home() / ".zshrc")
