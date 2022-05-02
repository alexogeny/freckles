function package_icon() {
  if (( $is_git )); then
    has_package="$(git rev-parse --show-toplevel)/package.json"
    if [ -f $has_package ]; then
      which jq > /dev/null
      if [ $? -eq 0 ]; then
        version_number="$(cat $has_package | jq .version | grep -Po '[0-9a-z\.]+')"
        if [[ ! $version_number =~ null ]]; then
          echo " %F{137}📦 ${version_number}%f"
        else
          echo " %F{137}📦 package%f"
        fi
      fi
    fi
  fi
}
