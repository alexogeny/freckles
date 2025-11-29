from __future__ import annotations

from pathlib import Path

from utils.debian import check_if_installed, run


def _bun_binary_path() -> Path:
    return Path.home() / ".bun" / "bin" / "bun"


def _global_bun_path() -> Path:
    return Path("/usr/local/bin/bun")


def is_bun_installed() -> bool:
    bun_binary = _bun_binary_path()
    return check_if_installed("bun") or bun_binary.exists()


def _ensure_global_bun_link() -> None:
    bun_binary = _bun_binary_path()
    if not bun_binary.exists():
        return

    global_path = _global_bun_path()
    if global_path.exists():
        try:
            if global_path.resolve() == bun_binary.resolve():
                return
        except FileNotFoundError:
            pass

    result = run(f"sudo ln -sf {bun_binary} {global_path}")
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        message = stderr or stdout or "unknown error"
        raise RuntimeError(f"Failed to link Bun globally: {message}")


def install_bun() -> None:
    if not is_bun_installed():
        install_result = run("curl -fsSL https://bun.sh/install | bash")
        if install_result.returncode != 0:
            stderr = (install_result.stderr or "").strip()
            stdout = (install_result.stdout or "").strip()
            message = stderr or stdout or "unknown error"
            raise RuntimeError(f"Failed to install Bun: {message}")

    _ensure_global_bun_link()

__all__ = ["install_bun", "is_bun_installed"]
