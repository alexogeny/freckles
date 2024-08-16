from pathlib import Path

from run import run


def open_repository_in_browser():
    current_directory = str(Path.cwd()).lower()
    url = None
    if "/github/" in current_directory:
        url = "https://github.com/" + current_directory.split("/github/")[-1]
        run(f"xdg-open {url}")
    elif "/gitlab/" in current_directory:
        url = "https://gitlab.com/" + current_directory.split("/gitlab/")[-1]
        run(f"xdg-open {url}")


if __name__ == "__main__":
    open_repository_in_browser()
