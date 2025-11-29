from __future__ import annotations

from pathlib import Path
from typing import Optional


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "firefox"
POLICIES_TEMPLATE = TEMPLATE_DIR / "policies.json"
USER_JS_TEMPLATE = TEMPLATE_DIR / "user.js"
HANDLERS_TEMPLATE = TEMPLATE_DIR / "handlers.json"
CONTAINERS_TEMPLATE = TEMPLATE_DIR / "containers.json"
USER_CHROME_TEMPLATE = TEMPLATE_DIR / "chrome" / "userChrome.css"


def read_template(path: Path, label: str) -> Optional[str]:
    if not path.exists():
        print(f"Missing Firefox {label} template at {path}. Skipping.")
        return None
    return path.read_text(encoding="utf-8")

