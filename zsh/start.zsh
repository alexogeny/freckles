#!/bin/bash

# Original input from $1
service=$1

# Strip all '.' characters
stripped_service="${service//./}"

if [ -z $stripped_service ]; then
  echo "Usage: spin-up <service>"
  exit 1
fi

value="${!stripped_service}"

IFS=' ' read -r service_dir service_port <<<"$value"

# Detect service type based on file existence
if [ -f "$service_dir/package.json" ]; then
  has_vite=$(cat "$service_dir/package.json" | jq -r .devDependencies.vite)
  echo "has vite $has_vite"
  if [[ "$has_vite" == "null" ]]; then
    package_name=$(cat "$service_dir/package.json" | jq -r .name)
    if [[ "$package_name" == "accounts-server" ]]; then
      cmd="export PORT=$service_port; cd $service_dir && bun run nest start"
    fi
  else
    cmd="cd $service_dir && npx vite dev --port=$service_port --host 127.0.0.1"
  fi
elif [ -f "$service_dir/pyproject.toml" ]; then
  if [ -f "$service_dir/dev.sh" ]; then
    if grep -q "docker" "$service_dir/dev.sh"; then
      docker_cmd="cd $service_dir/docker && docker compose up -d"
    else
      docker_cmd=""
    fi

    original_cmd=$(grep -Po "(?<=\()(pipenv run (python|uvicorn) .+? --port [0-9]+)(?=\))|pipenv run (python|uvicorn) .+? --port [0-9]+" "$service_dir/dev.sh" | head -n 1)
    if [[ ! -z "$original_cmd" ]]; then
      modified_cmd=$(echo "$original_cmd" | sed "s/--port [0-9]\+/--port $service_port/")
      if [[ $original_cmd == "("* ]]; then
        cmd="cd $service_dir && ($modified_cmd)"
      else
        cmd="cd $service_dir && $modified_cmd"
      fi
    else
      echo "No valid pipenv command found in $service_dir/dev.sh."
      exit 1
    fi

    if [ ! -z "$docker_cmd" ]; then
      cmd="$docker_cmd && $cmd"
    fi
  else
    echo "dev.sh not found in $service_dir."
    exit 1
  fi
else
  echo "No recognized service type (Node.js or Python) found in $service_dir."
  exit 1
fi

cmd="$cmd; echo 'Press enter to close...'; read"

gnome-terminal --tab --title="$service" -- /bin/bash -c "$cmd"
