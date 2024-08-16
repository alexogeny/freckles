import os
import sys
from pathlib import Path
from typing import Literal, get_args

from run import run

HostType = Literal["github", "gitlab"]
ContextType = Literal["private", "work"]


def clone_repository(
    repo,
    host: HostType = "github",
    context: ContextType = "private",
):
    if host not in get_args(HostType):
        raise ValueError(f"host arg should be one of {get_args(HostType)}")
    if context not in get_args(ContextType):
        raise ValueError(f"context arg should be one of {get_args(ContextType)}")
    home = os.path.expanduser("~")
    local = f"{home}/{context}/{host}/{repo}"
    if Path(local).exists():
        raise ValueError(f"looks like {local} already exists")
    else:
        Path(local).mkdir(parents=True)
    repo = f"git@{host}.com-{context}:{repo}.git"
    config = f"{home}/.{context}.{host}.gitconfig"
    run(f"git clone {repo} {local} --quiet --depth 15")
    os.chdir(local)
    run(f'git config --local include.path "{config}"')


if __name__ == "__main__":
    repo = sys.argv[1]
    host = sys.argv[2].replace("--", "")
    context = sys.argv[3].replace("--", "")

    clone_repository(repo, host, context)
