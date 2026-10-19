#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT_DIR}/.env"

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
HOST_IP="${HOST_IP:-127.0.0.1}"

cat > "${ROOT_DIR}/CREDENTIALS.md" <<EOF
# CodeLearn Platform — Учётные данные

Сгенерировано: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Веб-интерфейс

| Параметр | Значение |
|----------|----------|
| URL приложения | http://${HOST_IP}:${APP_PORT:-8000} |
| Django Admin | http://${HOST_IP}:${APP_PORT:-8000}/admin |
| Judge0 API | http://${HOST_IP}:${JUDGE0_PORT:-2358} |

## Суперадминистратор

| Поле | Значение |
|------|----------|
| Логин | ${INITIAL_ADMIN_USERNAME} |
| Пароль | ${INITIAL_ADMIN_PASSWORD} |
| Email | ${INITIAL_ADMIN_EMAIL} |

## Демо-ученик (Гоша)

| Поле | Значение |
|------|----------|
| Логин | ${DEMO_STUDENT_USERNAME} |
| Пароль | ${DEMO_STUDENT_PASSWORD} |
| Имя | ${DEMO_STUDENT_NAME} |

## PostgreSQL

| База | Пользователь | Пароль | Хост |
|------|--------------|--------|------|
| ${CODELEARN_DB_NAME} | ${CODELEARN_DB_USER} | ${CODELEARN_DB_PASS} | 127.0.0.1:5432 |
| ${JUDGE0_DB_NAME} | ${JUDGE0_DB_USER} | ${JUDGE0_DB_PASS} | 127.0.0.1:5432 |

## Redis

- Django/Celery: \`${REDIS_URL}\`
- Judge0: \`${JUDGE0_REDIS_URL}\`

## Прочее

- \`APP_SECRET_KEY\`: см. файл \`.env\`
- \`DATABASE_URL\`: \`${DATABASE_URL}\`
- \`JUDGE0_API_URL\`: \`${JUDGE0_API_URL}\`

## Запуск / остановка

\`\`\`bash
cd ${ROOT_DIR}
bash scripts/start-all.sh    # запуск всех сервисов
bash scripts/stop-all.sh     # остановка
bash scripts/smoke-test.sh   # проверка MVP
\`\`\`
EOF

chmod 600 "${ROOT_DIR}/CREDENTIALS.md"
echo "Wrote ${ROOT_DIR}/CREDENTIALS.md"
