function python_icon() {
  if (( $is_git )); then
    git_top_level=$(git rev-parse --show-toplevel)
    has_requirements_txt="$git_top_level/requirements.txt"
    has_pyproject_toml="$git_top_level/pyproject.toml"
    has_setup_py="$git_top_level/setup.py"
    if [[ -f $has_requirements_txt || -f $has_pyproject_toml || -f $has_setup_py ]]; then
      echo " %F{154}🐍 python%f"
    fi
  fi
}
