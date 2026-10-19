#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT_DIR}/.env"

BASE="http://127.0.0.1:${APP_PORT:-8000}"
COOKIE_JAR="/tmp/codelearn-smoke-cookies.txt"
rm -f "$COOKIE_JAR"

echo "==> Smoke test: login as admin"
LOGIN=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${INITIAL_ADMIN_USERNAME}\",\"password\":\"${INITIAL_ADMIN_PASSWORD}\"}" \
  "$BASE/api/auth/login")
echo "$LOGIN" | grep -q '"username"' && echo "  OK: admin login" || { echo "  FAIL: admin login"; exit 1; }

echo "==> Smoke test: languages"
curl -sf -b "$COOKIE_JAR" "$BASE/api/languages" | grep -q python && echo "  OK: languages" || { echo "  FAIL: languages"; exit 1; }

echo "==> Smoke test: courses"
curl -sf -b "$COOKIE_JAR" "$BASE/api/courses" | grep -q "Python" && echo "  OK: courses" || echo "  WARN: courses (may be empty for admin)"

echo "==> Smoke test: login as student"
rm -f "$COOKIE_JAR"
curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${DEMO_STUDENT_USERNAME}\",\"password\":\"${DEMO_STUDENT_PASSWORD}\"}" \
  "$BASE/api/auth/login" | grep -q "${DEMO_STUDENT_USERNAME}" && echo "  OK: student login" || { echo "  FAIL: student login"; exit 1; }

echo "==> Smoke test: student courses"
COURSES=$(curl -sf -b "$COOKIE_JAR" "$BASE/api/courses")
echo "$COURSES" | grep -q "Python" && echo "  OK: student sees course" || { echo "  FAIL: student courses"; exit 1; }

echo "==> Smoke test: leaderboard"
curl -sf -b "$COOKIE_JAR" "$BASE/api/leaderboard" > /dev/null && echo "  OK: leaderboard" || { echo "  FAIL: leaderboard"; exit 1; }

echo "==> Smoke test: Judge0"
curl -sf "http://127.0.0.1:${JUDGE0_PORT:-2358}/languages" | grep -q Python && echo "  OK: Judge0" || echo "  WARN: Judge0 not responding"

echo ""
echo "Smoke tests passed!"
