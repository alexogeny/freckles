function clone_repo() {
  # Usage: clone_repo [namespace/repo] [--gh|--gl] [--work]

  local namespace_repo="$1"
  local platform="$2"
  local work="$3"

  case "$work" in
    --work)
      local workspace="Work"
      local gitconfig_suffix=".work"
      local domain="-work"
      ;;
    *)
      local workspace="Personal"
      local gitconfig_suffix=""
      local domain=""
      ;;
  esac

  case "$platform" in
    --gh)
      local hostname="github.com${domain}"
      local target_base="${HOME}/${workspace}/Github"
      local gitconfig="${HOME}/.github${gitconfig_suffix}.gitconfig"
      ;;
    --gl)
      local hostname="gitlab.com${domain}"
      local target_base="${HOME}/${workspace}/Gitlab"
      local gitconfig="${HOME}/.gitlab${gitconfig_suffix}.gitconfig"
      ;;
    *)
      echo "Invalid platform. Please use --gh, or --gl."
      return 1
      ;;
  esac

  local repo_url="git@${hostname}:${namespace_repo}.git"
  local target_dir="${target_base}/${namespace_repo}"

  mkdir -p "$target_dir"
  export spinner_icon="🧬"
  export spinner_msg="Cloning to ${target_dir}"
  ~/.spinner git clone "$repo_url" "$target_dir" --quiet
  git --git-dir="$target_dir/.git" --work-tree="$target_dir" config --local include.path "$gitconfig"

}

alias gcl="clone_repo"

hg() {
  # open the current repo in the browser
  # hg = hosted git
  current_dir=$(pwd)
  if [[ $current_dir == *'Github'* ]]; then
    base_url='https://github.com'
  elif [[ $current_dir == *'Gitlab'* ]]; then
    base_url='https://gitlab.com'
  else
    echo "Neither Github nor Gitlab found in directory path."
    return 1
  fi

  repo_path=${current_dir#*Github/}
  repo_path=${repo_path#*Gitlab/}

  full_url="$base_url/$repo_path"

  xdg-open $full_url
}
