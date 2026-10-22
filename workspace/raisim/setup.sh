#!/usr/bin/env bash
set -euo pipefail
setup_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$setup_dir/../.." && pwd)"
workspace_dir="$(cd -- "$repo_dir/../.." && pwd)"
raisim_dir="$workspace_dir/third_party/raisimLib"
revision=afef6dc53a1a2c72fe824eeb32fa6930b50d4703
if [[ ! -e "$raisim_dir" ]]; then
  git clone --depth 1 --branch v1.1.7 https://github.com/raisimTech/raisimLib.git "$raisim_dir"
fi
actual="$(git -C "$raisim_dir" rev-parse HEAD)"
[[ "$actual" = "$revision" ]] || { echo "Unexpected RaiSim revision: $actual" >&2; exit 1; }
docker build --tag solo12_raisim_ws:base --file "$setup_dir/Dockerfile" "$setup_dir"
mkdir -p "$workspace_dir/docker/raisim/license"
if docker container inspect docker_solo12_raisim_ws >/dev/null 2>&1; then
  echo 'Container already exists; use docker start/exec docker_solo12_raisim_ws.'
  exit 0
fi
docker run -d --name docker_solo12_raisim_ws --hostname solo12-raisim \
  --mac-address 02:42:73:12:00:01 --init --shm-size=1g \
  --mount "type=bind,src=$workspace_dir,dst=$workspace_dir" \
  --mount "type=bind,src=$raisim_dir,dst=/opt/raisimLib,readonly" \
  --mount "type=bind,src=$workspace_dir/docker/raisim/license,dst=/home/$(id -un)/.raisim,readonly" \
  solo12_raisim_ws:base sleep infinity
