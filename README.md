# CodeLearn Platform

Self-hosted образовательная платформа для обучения программированию.

## Быстрый старт

```bash
cd /root/codelearn-platform

# Первоначальная установка (один раз)
bash scripts/generate-env.sh      # если .env ещё нет
bash scripts/install-system.sh
bash scripts/setup-postgres.sh
bash scripts/setup-redis.sh
bash scripts/setup-judge0.sh
bash scripts/setup-backend.sh

# Запуск
bash scripts/start-all.sh

# Проверка
bash scripts/smoke-test.sh

# Остановка
bash scripts/stop-all.sh
```

## Учётные данные

См. [CREDENTIALS.md](CREDENTIALS.md) — генерируется при запуске `start-all.sh`.

## Стек (без Docker)

- **Backend:** Django 5 + DRF + Celery
- **Frontend:** React 18 + Vite + Monaco Editor
- **БД:** PostgreSQL (codelearn + judge0)
- **Кеш/очереди:** Redis
- **Code runner:** Judge0 CE v1.13.1 (нативно + isolate)

## Порты

| Сервис | Порт |
|--------|------|
| Web UI + API | 8000 |
| Judge0 API | 2358 |
| PostgreSQL | 5432 |
| Redis | 6379 |

## Структура

```
codelearn-platform/
├── backend/          # Django API
├── frontend/         # React SPA
├── judge0/           # Judge0 CE source + isolate
├── data/seeds/       # Стартовый курс Python (24 урока)
├── scripts/          # Установка и запуск
└── CREDENTIALS.md    # Логины и пароли
```

## Telegram-бот (проверка решений)

Бот уведомляет преподавателей и админов о новых решениях и позволяет принимать / отклонять / комментировать / перепроверять прямо в Telegram.

Настройки хранятся в БД и редактируются в **админ-панели** платформы (раздел на главной `/admin`):

- включение бота
- токен от @BotFather
- username бота
- HTTP(S) proxy
- уведомления обо всех решениях или только `manual_review`

1. Создайте бота у [@BotFather](https://t.me/BotFather).
2. Войдите как admin/superadmin → Админ-панель → блок «Telegram-бот» → заполните и сохраните.
3. При смене токена/proxy перезапустите сервисы: `bash scripts/start-all.sh` (процесс бота всегда поднимается и ждёт настройки).
4. Создайте код привязки и отправьте боту `/start КОД`.
5. Команды бота: `/pending`, `/help`, `/unlink`, `/status`.

Опционально значения из `.env` (`TELEGRAM_BOT_*`) используются только как одноразовый seed при первом создании записи настроек.

## Примечания

- Judge0 требует Ruby 2.7.8 (установлен через rbenv в `/root/.rbenv`)
- isolate установлен в `/usr/local/bin/isolate`
- На Ubuntu 24.04 при проблемах с sandbox может потребоваться cgroups v1 (см. документацию Judge0)

