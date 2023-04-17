function clone_repo() {
  # Usage: clone_repo [namespace/repo] [--work-gh|--work-gl|--gh|--gl]

  local namespace_repo="$1"
  local platform="$2"

  case "$platform" in
    --work-gh)
      local hostname="work.github.com"
      local target_base="${HOME}/Work/Github"
      local gitconfig="${HOME}/.work.gitconfig"
      ;;
    --work-gl)
      local hostname="work.gitlab.com"
      local target_base="${HOME}/Work/Gitlab"
      local gitconfig="${HOME}/.work.gitconfig"
      ;;
    --gh)
      local hostname="github.com"
      local target_base="${HOME}/Personal/Github"
      local gitconfig="${HOME}/.github.gitconfig"
      ;;
    --gl)
      local hostname="gitlab.com"
      local target_base="${HOME}/Personal/Gitlab"
      local gitconfig="${HOME}/.gitlab.gitconfig"
      ;;
    *)
      echo "Invalid platform. Please use --work, --gh, or --gl."
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

alias gclone="clone_repo"
