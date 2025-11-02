alias auu="apt-update-upgrade"
alias ai="apt-install"

alias ghw="cd ~/Work/Github"
alias glw="cd ~/Work/Gitlab"
alias ghp="cd ~/Personal/Github"
alias glp="cd ~/Personal/Gitlab"

alias ls="ls --color=auto"
function cs() {
    cd "$1" && ls
}

function nn() {
    local target_dir
    if [ $# -eq 0 ]; then
        target_dir=$(uv run --no-project ~/.shell/dynamic_navigate.py)
    else
        target_dir=$(uv run --no-project ~/.shell/dynamic_navigate.py "$*")
    fi
    local status=$?
    if [ $status -eq 0 ] && [ -n "$target_dir" ]; then
        cd "$target_dir" || echo "Failed to change directory"
    else
        echo "Failed to determine target directory"
        return $status
    fi
}

alias ..='cs ..'
alias ...='cs ../..'
alias ....='cs ../../..'
alias .....='cs ../../../..'
alias ......='cs ../../../../..'
alias .......='cs ../../../../../..'

alias c='clear'

alias ll='ls -la'
alias l.='ls -d .* --color=auto'
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'

alias sha1='openssl sha1'
alias sha256='openssl sha256'
alias sha512='openssl sha512'

alias mdp='mkdir -pv'

alias mv='mv -i'
alias ln='ln -i'

alias python=python3
alias pip=pip3

alias gpl="git pull --rebase --autostash --prune"
alias gps="git push"
alias gpsf="git push --force-with-lease"
alias gfs="git fs"
alias grb="git rb"
alias gdb="git db"
