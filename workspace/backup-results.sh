#!/usr/bin/env bash
# Explicitly selected local artifacts; never credentials or licenses.
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:?Usage: bash workspace/backup-results.sh /absolute/path/results.tar.gz}"
[[ "$target" = /* ]] || { echo 'Use an absolute archive path.' >&2; exit 1; }
test ! -e "$target" || { echo "Archive exists: $target" >&2; exit 1; }
tar -czf "$target" -C "$repo_dir" paper/results paper/checks
sha256sum "$target"
