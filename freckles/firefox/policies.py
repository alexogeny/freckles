from __future__ import annotations

import shlex

from utils.debian import run
from .templates import POLICIES_TEMPLATE, read_template


def apply_firefox_policies() -> None:
    template_contents = read_template(POLICIES_TEMPLATE, "policies.json")
    if template_contents is None:
        return

    policies_dir = "/etc/firefox/policies"
    policies_path = f"{policies_dir}/policies.json"

    create_dir = run(["sudo", "install", "-d", "-m", "0755", policies_dir])
    write_policy = run(
        f"echo {shlex.quote(template_contents)} | sudo tee {policies_path}"
    )
    set_perms = run(["sudo", "chmod", "0644", policies_path])
    if any(result.returncode != 0 for result in (create_dir, write_policy, set_perms)):
        print("Failed to apply Firefox policies.")
        return
    print("Applied Firefox enterprise policies template.")

