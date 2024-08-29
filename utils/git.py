from .meta import HOME, REPOSITORY_LATEST
from .web import download_file


def configure_git():
    for filename in [
        ".gitconfig",
        ".gitignore",
        ".private.gitlab.gitconfig",
        ".private.github.gitconfig",
    ]:
        local_path = HOME / filename
        if not local_path.exists():
            download_file(
                REPOSITORY_LATEST + "git/" + filename,
                local_path,
            )
