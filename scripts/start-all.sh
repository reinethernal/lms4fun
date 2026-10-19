#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
PID_DIR="${ROOT_DIR}/pids"
JUDGE0_DIR="${ROOT_DIR}/judge0/judge0-src"
BACKEND_DIR="${ROOT_DIR}/backend"

mkdir -p "$LOG_DIR" "$PID_DIR"

# shellcheck source=/dev/null
source "${ROOT_DIR}/.env"

stop_pid() {
  local name="$1"
  local pidfile="${PID_DIR}/${name}.pid"
  if [[ -f "$pidfile" ]]; then
    kill "$(cat "$pidfile")" 2>/dev/null || true
    rm -f "$pidfile"
  fi
}

echo "==> Stopping existing processes..."
for svc in judge0-worker judge0-server celery django telegram-bot; do
  stop_pid "$svc"
done

echo "==> Rotating log files..."
bash "${ROOT_DIR}/scripts/rotate-logs.sh"

echo "==> Starting PostgreSQL and Redis..."
systemctl start postgresql redis-server

echo "==> Starting Judge0..."
# shellcheck source=/dev/null
source "${ROOT_DIR}/judge0/judge0.env"

cd "$JUDGE0_DIR"
BUNDLE="bundle"
nohup $BUNDLE exec rails server -b 0.0.0.0 -p "${JUDGE0_PORT:-2358}" \
  > "${LOG_DIR}/judge0-server.log" 2>&1 &
echo $! > "${PID_DIR}/judge0-server.pid"

nohup $BUNDLE exec rake resque:work QUEUE="${JUDGE0_VERSION}" COUNT=2 \
  > "${LOG_DIR}/judge0-worker.log" 2>&1 &
echo $! > "${PID_DIR}/judge0-worker.pid"

sleep 8

echo "==> Starting Django and Celery..."
cd "$BACKEND_DIR"
source .venv/bin/activate

nohup celery -A config worker -l info > /dev/null 2>&1 &
echo $! > "${PID_DIR}/celery.pid"

nohup python manage.py runserver "${APP_HOST:-0.0.0.0}:${APP_PORT:-8000}" > /dev/null 2>&1 &
echo $! > "${PID_DIR}/django.pid"

# Always start; command waits until settings are configured in admin panel
nohup python manage.py run_telegram_bot > "${LOG_DIR}/telegram-bot.log" 2>&1 &
echo $! > "${PID_DIR}/telegram-bot.pid"
echo "Telegram bot: starting (settings via admin panel)"

sleep 3

echo "==> Health checks..."
curl -sf "http://127.0.0.1:${JUDGE0_PORT:-2358}/languages" > /dev/null && echo "Judge0: OK" || echo "Judge0: FAIL"
curl -sf "http://127.0.0.1:${APP_PORT:-8000}/api/languages" > /dev/null && echo "Django API: OK" || echo "Django API: FAIL"

bash "${ROOT_DIR}/scripts/write-credentials.sh"

echo ""
echo "Platform started!"
echo "  App:    http://127.0.0.1:${APP_PORT:-8000}"
echo "  Judge0: http://127.0.0.1:${JUDGE0_PORT:-2358}"
echo "  Creds:  ${ROOT_DIR}/CREDENTIALS.md"
