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
    host_arg, context_arg = host, context
    if host not in get_args(HostType):
        if host in get_args(ContextType):
            context_arg = host
        else:
            raise ValueError(f"host arg should be one of {get_args(HostType)}")
    if context not in get_args(ContextType):
        if context in get_args(HostType):
            host_arg = context
        else:
            raise ValueError(f"context arg should be one of {get_args(ContextType)}")
    home = os.path.expanduser("~")
    local = f"{home}/{context_arg}/{host_arg}/{repo}"
    if Path(local).exists():
        raise ValueError(f"looks like {local} already exists")
    else:
        Path(local).mkdir(parents=True)
    repo = f"git@{host_arg}.com-{context_arg}:{repo}.git"
    config = f"{home}/.{context_arg}.{host_arg}.gitconfig"
    run(f"git clone {repo} {local} --quiet --depth 15")
    os.chdir(local)
    run(f'git config --local include.path "{config}"')


if __name__ == "__main__":
    repo = sys.argv[1]
    host = sys.argv[2].replace("--", "")
    context = sys.argv[3].replace("--", "")

    clone_repository(repo, host, context)
