#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_dir="$(cd -- "$repo_dir/../.." && pwd)"
auth_file="${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}"
test -f "$auth_file" || { echo "Xauthority missing: $auth_file" >&2; exit 1; }
exec docker run --rm --gpus all --name docker_solo12_teleop \
  -e DISPLAY="${DISPLAY:?DISPLAY must be set}" \
  -e XAUTHORITY=/tmp/solo12.xauth -e MUJOCO_GL=glfw \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics,display \
  -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 \
  --mount type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly \
  --mount "type=bind,src=$auth_file,dst=/tmp/solo12.xauth,readonly" \
  --mount "type=bind,src=$workspace_dir,dst=$workspace_dir" \
  -w "$repo_dir" solo12_rl_ws:base python3 -m demo.teleop "$@"
