# export PYENV_ROOT="$HOME/.pyenv"
# command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init -)"

# export PATH="$HOME/.local/bin:$PATH"

export CFLAGS="-I$(brew --prefix openssl)/include"
export LDFLAGS="-L$(brew --prefix openssl)/lib"

# source "$HOME/.rye/env"
export PATH="$HOME/.rye/shims:$PATH"
