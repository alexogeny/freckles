function php_icon() {
  if (( $is_git )); then
    has_composer="$(git rev-parse --show-toplevel)/composer.json"
    if [ -f $has_composer ]; then
      which jq > /dev/null
      if [ $? -eq 0 ]; then
        versionNumber="$(cat $has_composer | jq .require.php | grep -Po '[0-9a-z\.]+')"
        php_icon=" %F{147}🐘 php ${versionNumber}%f"
      else
        php_icon=" %F{147}🐘 php%f"
      fi
    fi
  fi
}
