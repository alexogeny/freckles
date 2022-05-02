function yarn_icon() {
  if (( $is_git )); then
    has_yarn="$(git rev-parse --show-toplevel)/yarn.lock"
    if [ -f $has_yarn ]; then
      echo " %F{161}🧶 yarn%f"
    fi
  fi
}
