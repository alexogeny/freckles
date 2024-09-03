import textwrap

from .debian import run
from .meta import KNOWN_HOSTS, SSH_CONFIG, SSH_DIR
from .one_password import ensure_op_connected

known_hosts_content = textwrap.dedent("""
gitlab.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAfuCHKVTjquxvt6CM6tdG4SLp1Btn/nOeHHE5UOzRdf
gitlab.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsj2bNKTBSpIYDEGk9KxsGh3mySTRgMtXL583qmBpzeQ+jqCMRgBqB98u3z++J1sKlXHWfM9dyhSevkMwSbhoR8XIq/U0tCNyokEi/ueaBMCvbcTHhO7FcwzY92WK4Yt0aGROY5qX2UKSeOvuP4D6TPqKF1onrSzH9bx9XUf2lEdWT/ia1NEKjunUqu1xOB/StKDHMoX4/OKyIzuS0q/T1zOATthvasJFoPrAjkohTyaDUz2LN5JoH839hViyEG82yB+MjcFV5MU3N1l1QL3cVUCh93xSaua1N85qivl+siMkPGbO5xR/En4iEY6K2XPASUEMaieWVNTRCtJ4S8H+9
gitlab.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBFSMqzJeV9rUzU4kWitGjeR4PWSa29SPqJ1fVkhtj3Hw9xjLVXVYrU9QlYWrOLXBpQ6KWjbjTDTdDkoohFzgbEY=

github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=
github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=
""")


def get_favorite_git_items():
    ensure_op_connected()
    return [
        i
        for i in run("op item list --favorite").stdout.lower().splitlines()
        if "git" in i
    ]


def write_known_hosts():
    if not KNOWN_HOSTS.exists():
        KNOWN_HOSTS.write_text(known_hosts_content)


def setup_ssh_key(vault, git_provider, item_list):
    matching_item = next(
        (i for i in item_list if vault in i and git_provider in i), None
    )
    if matching_item:
        key = SSH_DIR / f"{vault}.{git_provider}"
        op_path = f"op://{vault}/{git_provider}/ssh"
        run(f'op read --force --out-file "{key}.pub" "{op_path}/public"')
        run(f'op read --force --out-file "{key}" "{op_path}/private"')
        run(f'ssh-add "{key}"')


def add_ssh_config(vault, git):
    config_entry = textwrap.dedent(f"""
        Host {git}.com-{vault}
            HostName {git}.com
            AddKeysToAgent yes
            IdentityFile ~/.ssh/{vault}.{git}
            User git
    """)
    with SSH_CONFIG.open("a") as fh:
        fh.write(config_entry)


def configure_ssh():
    write_known_hosts()
    item_list = []
    existing_config = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    for vault in ["private", "work"]:
        for git_provider in ["github", "gitlab"]:
            if f"Host {git_provider}.com-{vault}" in existing_config:
                continue
            if len(item_list) == 0:
                item_list = get_favorite_git_items()
            setup_ssh_key(vault, git_provider, item_list)
            add_ssh_config(vault, git_provider)
