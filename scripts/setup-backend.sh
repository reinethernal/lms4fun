#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
LOG_DIR="${ROOT_DIR}/logs"
PID_DIR="${ROOT_DIR}/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

# shellcheck source=/dev/null
source "${ROOT_DIR}/.env"

echo "==> Setting up backend..."
cd "$BACKEND_DIR"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r requirements.txt
python manage.py migrate --noinput
python manage.py seed_platform
python manage.py collectstatic --noinput 2>/dev/null || true

echo "==> Building frontend..."
cd "$FRONTEND_DIR"
if [[ ! -d node_modules ]]; then
  npm install --silent
fi
npm run build --silent

bash "${ROOT_DIR}/scripts/setup-compiler-symlinks.sh"

# Copy frontend build to Django static
mkdir -p "${BACKEND_DIR}/static"
cp -r dist/* "${BACKEND_DIR}/static/"
python manage.py collectstatic --noinput 2>/dev/null || true

echo "==> Backend setup complete."
