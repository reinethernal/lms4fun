#!/usr/bin/env bash
# Rotate log files on service restart; keep 7 versions per stream (6 backups + active).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
MAX_BACKUPS=6

mkdir -p "$LOG_DIR"

rotate_one() {
  local base="$1"
  local file="${LOG_DIR}/${base}.log"
  [[ -f "$file" ]] || return 0
  [[ -s "$file" ]] || return 0

  local ts
  ts="$(date +%Y%m%d-%H%M%S)"
  mv "$file" "${file}.${ts}"

  # Remove oldest timestamped backups beyond MAX_BACKUPS.
  mapfile -t old_files < <(ls -1t "${file}".[0-9]* 2>/dev/null || true)
  if ((${#old_files[@]} > MAX_BACKUPS)); then
    for stale in "${old_files[@]:MAX_BACKUPS}"; do
      rm -f "$stale"
    done
  fi
}

for stream in django celery submissions errors judge0-server judge0-worker; do
  rotate_one "$stream"
done
