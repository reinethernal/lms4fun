#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JUDGE0_DIR="${ROOT_DIR}/judge0/judge0-src"
ISOLATE_DIR="${ROOT_DIR}/judge0/isolate"
# shellcheck source=/dev/null
source "${ROOT_DIR}/.env"

echo "==> Building isolate sandbox..."
if [[ ! -d "$ISOLATE_DIR" ]]; then
  git clone --depth 1 https://github.com/judge0/isolate.git "$ISOLATE_DIR"
fi
make -C "$ISOLATE_DIR" isolate
make -C "$ISOLATE_DIR" install
isolate --init || true
isolate --cg || true

echo "==> Installing Judge0 Ruby gems..."
cd "$JUDGE0_DIR"
export POSTGRES_HOST="${JUDGE0_DB_HOST}"
export POSTGRES_PORT="${JUDGE0_DB_PORT}"
export POSTGRES_DB="${JUDGE0_DB_NAME}"
export POSTGRES_USER="${JUDGE0_DB_USER}"
export POSTGRES_PASSWORD="${JUDGE0_DB_PASS}"
export REDIS_HOST="127.0.0.1"
export REDIS_PORT="6379"
export REDIS_PASSWORD=""
export RAILS_ENV="${JUDGE0_RAILS_ENV:-production}"
export RAILS_MAX_THREADS=2
export RAILS_SERVER_PROCESSES=1
export PORT="${JUDGE0_PORT:-2358}"

bundle config set --local path vendor/bundle
bundle install --jobs 2

echo "==> Judge0 database setup..."
bundle exec rails db:create 2>/dev/null || true
bundle exec rails db:migrate
bundle exec rails db:seed

# Save judge0 env for start script
cat > "${ROOT_DIR}/judge0/judge0.env" <<EOF
export POSTGRES_HOST=${JUDGE0_DB_HOST}
export POSTGRES_PORT=${JUDGE0_DB_PORT}
export POSTGRES_DB=${JUDGE0_DB_NAME}
export POSTGRES_USER=${JUDGE0_DB_USER}
export POSTGRES_PASSWORD=${JUDGE0_DB_PASS}
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export REDIS_PASSWORD=
export RAILS_ENV=${JUDGE0_RAILS_ENV:-production}
export RAILS_MAX_THREADS=2
export RAILS_SERVER_PROCESSES=1
export PORT=${JUDGE0_PORT:-2358}
export ALLOW_ORIGIN=*
EOF

echo "==> Judge0 setup complete."
