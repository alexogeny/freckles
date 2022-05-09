#!/usr/bin/env zsh

setopt promptsubst

# cd & ls
alias ls='ls --color=auto'
LS_COLORS='no=00;37:fi=00:di=00;33:ln=04;36:pi=40;33:so=01;35:bd=40;33;01:'
export LS_COLORS
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}

auto-ls () {
  emulate -L zsh
  ls
}
chpwd_functions=(${chpwd_functions[@]} "auto-ls")

# git

## check that git is installed on the system and this is a git repo
check_git() {
  git check-ignore -q . 2> /dev/null
  (( is_git = $? == 1 ))
}
chpwd_functions+=(check_git)

## check if the branch is dirty using git porcelain
function parse_git_dirty {
  [[ -z $(git status --porcelain 2> /dev/null ) ]] || echo "%F{221}*"
}

## find the name of the branch we are currently on
function parse_git_branch {
  if (( $is_git )); then
    branch_name=$(git branch --no-color | sed -e '/^[^*]/d' | awk '{sub(/^[^[:alnum:]_]*/, ""); print $1}')
    echo "(%F{076}$branch_name$(parse_git_dirty)%F{039})"
  fi
}

# general
alias reboot='sudo reboot'
alias shutdown='sudo shutdown'
alias cl='clear'
alias rain='curl -s "wttr.in/Brisbane?format=3"'

# hashing
alias sha1='openssl sha1'
alias sha256='openssl sha256'

# grep
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'

# python
alias python='python3'
alias pip='pip3'
alias pipi='sudo pip install'

# apt
alias apti='sudo apt install'
alias aptu='sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y'

# remove old linux kernel
function kclean() {
  current="$(uname -r | awk -F '-generic' '{ print $1}')"
  installed="linux-(headers|image)-(${current}|$(uname -r)|generic)"
  removable=$(dpkg --list | egrep -i 'linux-image|linux-headers' | awk '/ii/{ print $2}' | egrep -v "$installed")
  sudo apt --purge remove $(echo $removable)
}

# docker
alias dc='docker compose'
alias dcrunl='dc run local'
alias dcupl='dc up local'
alias dcupd='dc up -d local'

function dst() {
  export spinner_msg="Stopping containers..."
  export spinner_icon="🐋"
  export up_count=$(docker ps -q | wc -l)
  if [[ $up_count -ne 0 ]]; then
    ~/.spinner docker stop $(docker ps -q)
  else echo " ${spinner_icon} ⠿ No containers to stop."
  fi
}

function drc() {
  export spinner_msg="Removing containers..."
  export spinner_icon="🐋"
  export up_count=$(docker ps -aq | wc -l)
  if [[ $up_count -ne 0 ]]; then
    ~/.spinner docker rm $(docker ps -aq)
  else
    echo " ${spinner_icon} ⠿ No containers to remove."
  fi
}
function dri() {
  export spinner_msg="Removing images..."
  export spinner_icon="🐋"
  export up_count=$(docker images -q | wc -l)
  if [[ $up_count -ne 0 ]]; then
    ~/.spinner docker rmi $(docker images -q)
  else
    echo " ${spinner_icon} ⠿ No images to remove."
  fi
}
function drv() {
  export spinner_msg="Removing volumes..."
  export spinner_icon="🐋"
  export up_count=$(docker volume ls -qf dangling=true | wc -l)
  if [[ $up_count -ne 0 ]]; then
    ~/.spinner docker volume rm $(docker volume ls -qf dangling=true)
  else
    echo " ${spinner_icon} ⠿ No volumes to remove."
  fi
}
alias dcyarn='docker compose run --rm local yarn'

## handy function to remove all traces of a docker container and images (will need tor epull)
function dpurge() {
  dst && drc && dri && drv
}
## similar to above but keeps cached images
function dclean() {
  dst && drc && drv
}


alias gpatch='git add --patch'
## switch to the main branch, regardless of its name
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

## push the branch and create an mr
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

## push to current branch
function_gpushc() {
  branch_current=$(git branch --show-current)
  echo "pushing to: $branch_current"
  git push -v -u origin $branch_current
}
alias gpushc='function_gpushc'

# link plugins to the prompt (for pretty icons)
for file in /home/alexogeny/.zsh/*; do
  source "$file"
done


# timing
function preexec() {
  timer=$(date +%s%3N)
}

function precmd() {
  if [ $timer ]; then
    local now=$(date +%s%3N)
    local d_ms=$(($now-$timer))
    local d_s=$((d_ms / 1000))
    local ms=$((d_ms % 1000))
    local s=$((d_s % 60))
    local m=$(((d_s / 60) % 60))
    local h=$((d_s / 3600))
    if ((h > 0)); then elapsed=${h}h${m}m
    elif ((m > 0)); then elapsed=${m}m${s}s
    elif ((s >= 10)); then elapsed=${s}.$((ms / 100))s
    elif ((s > 0)); then elapsed=${s}.$((ms / 10))s
    else elapsed=${ms}ms
    fi

    export RPROMPT="%F{cyan}${elapsed} %{$reset_color%}"
    unset timer
  fi
}

# theming
NL=$'\n'

PROMPT='%F{099}%n@%m%f in %F{039}%~$(parse_git_branch)'
PROMPT=$PROMPT$'$(docker_icon)$(python_icon)$(php_icon)$(package_icon)$(node_icon)$(yarn_icon)$(typescript_icon)${NL}%F{039}%(!.#.»)%f '
PROMPT=$'%(?..%{%F{202}%}%{$reset_color%})%F{237}${(r:$COLUMNS::-:)}'$PROMPT
