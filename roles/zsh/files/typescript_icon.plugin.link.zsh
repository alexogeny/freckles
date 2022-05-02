function typescript_icon() {
  if (( $is_git )); then
    has_tsconfig="$(git rev-parse --show-toplevel)/tsconfig.json"
    if [[ -f $has_tsconfig ]]; then
      echo " %F{060}🧷 typescript%f"
    fi
  fi
}
