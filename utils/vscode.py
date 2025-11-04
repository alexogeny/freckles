import json
import shutil
from pathlib import Path


SETTINGS_SOURCE = Path("./vscode/settings.link.json")
KEYBINDINGS_SOURCE = Path("./vscode/keybinds.link.json")
THEME_SOURCE = Path("./vscode/freckles-theme")


def _synchronise_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        raise FileNotFoundError(f"Missing VS Code template: {source}")

    if destination.exists() and destination.read_text(encoding="utf-8") == source.read_text(
        encoding="utf-8"
    ):
        return

    shutil.copy2(source, destination)


def _install_theme_extension(source: Path) -> None:
    if not source.exists():
        return

    manifest_path = source / "package.json"
    if not manifest_path.exists():
        raise FileNotFoundError("VS Code theme manifest not found")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = manifest.get("name")
    version = manifest.get("version")
    if not name or not version:
        raise ValueError("Theme manifest must include name and version")

    extensions_dir = Path.home() / ".vscode" / "extensions"
    extensions_dir.mkdir(parents=True, exist_ok=True)

    target = extensions_dir / f"{name}-{version}"
    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(source, target)

    for existing in extensions_dir.glob(f"{name}-*"):
        if existing == target or not existing.is_dir():
            continue
        shutil.rmtree(existing)


def configure_vscode():
    vscode = Path.home() / ".config" / "Code" / "User"
    settings, keybindings = vscode / "settings.json", vscode / "keybindings.json"
    _synchronise_file(SETTINGS_SOURCE, settings)
    _synchronise_file(KEYBINDINGS_SOURCE, keybindings)
    _install_theme_extension(THEME_SOURCE)
