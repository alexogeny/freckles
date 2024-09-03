import subprocess
from textwrap import dedent

from .meta import HOME, REPOSITORY_LATEST
from .web import download_file


def setup_work_gitconfig():
    work_gitlab_gitconfig = HOME / ".work.gitlab.gitconfig"
    work_github_gitconfig = HOME / ".work.github.gitconfig"
    if work_gitlab_gitconfig.exists() or work_github_gitconfig.exists():
        return
    platform = input("Select git platform (github or gitlab): ")
    email = input("Enter work git email: ")
    name = input("Enter work git username: ")
    gitconfig = dedent(
        """
        [user]
            name = {name}
            email = {email}
        """.format(name=name.strip().lower(), email=email.strip().lower())
    )
    outfile = (
        work_github_gitconfig
        if platform.lower().strip() == "github"
        else work_gitlab_gitconfig
    )
    subprocess.run(
        ["tee", outfile.as_posix()],
        input=gitconfig.encode("utf-8"),
        check=True,
    )


def download_git_files():
    for filename in [
        ".gitconfig",
        ".gitignore",
        ".private.gitlab.gitconfig",
        ".private.github.gitconfig",
    ]:
        local_path = HOME / filename
        if local_path.exists():
            continue
        download_file(
            REPOSITORY_LATEST + "git/" + filename,
            local_path,
        )


def configure_git():
    download_git_files()
    setup_work_gitconfig()
