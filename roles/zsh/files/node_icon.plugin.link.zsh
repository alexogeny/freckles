function node_icon() {
  if (( $is_git )); then
    git_top_level=$(git rev-parse --show-toplevel)
    has_package_json="$git_top_level/package.json"
    has_nvmrc="$git_top_level/.nvmrc"
    has_npmrc="$git_top_level/.npmrc"
    has_node_modules="$git_top_level/node_modules"
    if [[ -f $has_package_json || -f $has_nvmrc || -f $has_npmrc || -d $has_node_modules ]]; then
      echo " %F{041}🌱 node%f"
    fi
  fi
}
