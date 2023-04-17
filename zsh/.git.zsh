function clone_repo() {
  # Usage: clone_repo [namespace/repo] [--gh|--gl] [--work]

  local namespace_repo="$1"
  local platform="$2"
  local work="$3"

  case "$work" in
    --work)
      local workspace="Work"
      local gitconfig_suffix=".work"
      ;;
    *)
      local workspace="Personal"
      local gitconfig_suffix=""
      ;;
  esac

  case "$platform" in
    --gh)
      local hostname="github.com"
      local target_base="${HOME}/${workspace}/Github"
      local gitconfig="${HOME}/.github${gitconfig_suffix}.gitconfig"
      ;;
    --gl)
      local hostname="gitlab.com"
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

  echo "Cloning repository $repo_url to $target_dir"
  echo "Using gitconfig $gitconfig"

  mkdir -p "$target_dir"
  git clone "$repo_url" "$target_dir"
  git --git-dir="$target_dir/.git" --work-tree="$target_dir" config --local include.path "$gitconfig"

  echo "Repository cloned to $target_dir"
}

alias gcl="clone_repo"
