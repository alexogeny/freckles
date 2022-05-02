function docker_icon() {
  if (( $is_git )); then
    git_top_level=$(git rev-parse --show-toplevel)
    has_dcompose="$git_top_level/docker-compose.yml"
    has_compose="$git_top_level/compose.yml"
    has_dockerfile="$git_top_level/dockerfile"
    if [[ -f $has_dcompose || -f $has_compose || -f $has_dockerfile ]]; then
      echo " %F{075}🐋 docker%f"
    fi
  fi
}
