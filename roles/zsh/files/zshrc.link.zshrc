#!/usr/bin/env zsh

setopt promptsubst

auto-ls () {
  emulate -L zsh
  ls -a
}
chpwd_functions=(${chpwd_functions[@]} "auto-ls")

# git
check_git() {
  git check-ignore -q . 2> /dev/null
  (( is_git = $? == 1 ))
}
chpwd_functions+=(check_git)

# python
alias python='python3'
alias pip='pip3'

# apt
alias apti='sudo apt install'
alias aptu='sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y'

# docker
alias dc='docker compose'
alias dcrunl='dc run local'
alias dcupl='dc up local'
alias dcupd='dc up -d local'
alias dstop='docker stop $(docker ps -aq)'
alias dremc='docker rm $(docker ps -aq)'
alias dremi='docker rmi $(docker images -q)'
alias dremv='docker volume rm $(docker volume ls -qf dangling=true)'
alias dcyarn='docker compose run --rm local yarn'
function_dclean() {
  dstop
  dremc
  dremi
  dremv
}
alias dclean='function_dclean'


# git
alias gpatch='git add --patch'
function_gmain() {
  branch_main=$(git symbolic-ref --short refs/remotes/origin/HEAD | awk -F'/' '{print $2}')
  branch_current=$(git branch --show-current)
  if [ $(echo $branch_current | grep -c $branch_main) -eq 0 ]; then
    git checkout $branch_main
  else
    echo "already on $branch_main"
  fi
}
alias gmain='function_gmain'
function_gpushmr() {
  branch_current=$(git branch --show-current)
  echo "current branch: $branch_current"
  git push -v -u origin $branch_current \
    -o merge_request.create \
    -o merge_request.remove_source_branch \
    -o merge_request_target="$(git symbolic-ref --short refs/remotes/origin/HEAD | awk -F'/' '{print $2}')" \
    -o merge_request.assignee=$(git config user.name) \
    --force-with-lease
}
alias gpushmr='function_gpushmr'
function_gpushc() {
  branch_current=$(git branch --show-current)
  echo "pushing to: $branch_current"
  git push -v -u origin $branch_current
}
alias gpushc='function_gpushc'

# plugins
plugins=(git docker_icon node_icon package_icon php_icon python_icon typescript_icon yarn_icon)
export ZSH="$HOME/.oh-my-zsh"
source $ZSH/oh-my-zsh.sh

# theming
NL=$'\n'

PS1='%F{099}%n@%m%f in %F{039}%~$(git_prompt_info)$docker_icon$php_icon$package_icon$python_icon$node_icon$yarn_icon$typescript_icon${NL}$FG[105]%(!.#.»)%{$reset_color%} '
PS2='%{$fg[red]%}\ %{$reset_color%}'
RPS1='${return_code}'
PS1=$'$my_gray${(r:$COLUMNS::-:)}'$PS1

typeset +H return_code="%(?..%{$fg[red]%}%? ↵%{$reset_color%})"
typeset +H my_gray="$FG[237]"
typeset +H my_orange="$FG[214]"

ZSH_THEME_GIT_PROMPT_PREFIX="$FG[075]($FG[078]"
ZSH_THEME_GIT_PROMPT_CLEAN=""
ZSH_THEME_GIT_PROMPT_DIRTY="$my_orange*%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="$FG[075])%{$reset_color%}"

BLUE='\033[0;34m'
NC='\033[0m'
