#!/usr/bin/env bash
# Recreate this exact checkout plus its pinned dependencies on another machine.
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:?Usage: bash workspace/recreate.sh /absolute/path/solo12_rl_ws}"
[[ "$target" = /* ]] || { echo 'Use an absolute target path.' >&2; exit 1; }
revision="$(git -C "$repo_dir" rev-parse HEAD)"
destination="$target/src/solo12-locomotion"
if [[ "$destination" != "$repo_dir" ]]; then
  test ! -e "$destination" || { echo "Already exists: $destination" >&2; exit 1; }
  mkdir -p "$target/src"
  git clone https://github.com/giulianodejulio/solo12-locomotion.git "$destination"
  git -C "$destination" checkout --detach "$revision"
fi
cd "$destination"
bash workspace/bootstrap.sh
bash workspace/build.sh
bash workspace/run.sh
docker exec -w "$destination" "${SOLO12_CONTAINER:-docker_solo12_rl_ws}" python3 -m paper.validate
