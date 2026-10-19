"""Django settings for CodeLearn platform."""
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / '.env')

SECRET_KEY = os.getenv('APP_SECRET_KEY', 'django-insecure-dev-key-change-me')
DEBUG = os.getenv('APP_DEBUG', 'false').lower() in ('1', 'true', 'yes')
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('APP_DOMAIN', 'localhost').split(',')
    if host.strip()
]
if DEBUG:
    ALLOWED_HOSTS.extend(['127.0.0.1', '0.0.0.0', 'localhost', 'testserver'])

# COOP requires HTTPS on non-localhost origins; disable on plain HTTP deployments
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
USE_X_FORWARDED_HOST = os.getenv('USE_X_FORWARDED_HOST', 'true').lower() in ('1', 'true', 'yes')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'apps.accounts',
    'apps.courses',
    'apps.lessons',
    'apps.tasks',
    'apps.submissions',
    'apps.gamification',
    'apps.imports',
    'apps.notifications',
    'apps.telegram',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

database_url = os.getenv('DATABASE_URL', 'postgresql://codelearn:codelearn@127.0.0.1:5432/codelearn')
parsed_db = urlparse(database_url)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed_db.path.lstrip('/') or 'codelearn',
        'USER': parsed_db.username or 'codelearn',
        'PASSWORD': parsed_db.password or '',
        'HOST': parsed_db.hostname or '127.0.0.1',
        'PORT': parsed_db.port or 5432,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

_app_domains = [
    host.strip()
    for host in os.getenv('APP_DOMAIN', 'localhost').split(',')
    if host.strip()
]
CORS_ALLOWED_ORIGINS = []
for host in _app_domains:
    CORS_ALLOWED_ORIGINS.extend([f'http://{host}', f'https://{host}'])
CORS_ALLOWED_ORIGINS.extend([
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CORS_ALLOWED_ORIGINS))

CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

JUDGE0_API_URL = os.getenv('JUDGE0_API_URL', 'http://127.0.0.1:2358')
JUDGE0_API_TOKEN = os.getenv('JUDGE0_API_TOKEN', '')
CODE_RUN_TIME_LIMIT = float(os.getenv('CODE_RUN_TIME_LIMIT', '3'))
CODE_RUN_MEMORY_LIMIT = int(os.getenv('CODE_RUN_MEMORY_LIMIT', '128000'))
CODE_RUN_OUTPUT_LIMIT = int(os.getenv('CODE_RUN_OUTPUT_LIMIT', '20000'))

INITIAL_ADMIN_USERNAME = os.getenv('INITIAL_ADMIN_USERNAME', 'admin')
INITIAL_ADMIN_PASSWORD = os.getenv('INITIAL_ADMIN_PASSWORD', 'admin')
INITIAL_ADMIN_EMAIL = os.getenv('INITIAL_ADMIN_EMAIL', 'admin@localhost')
CREATE_DEMO_STUDENT = os.getenv('CREATE_DEMO_STUDENT', 'true').lower() in ('1', 'true', 'yes')
DEMO_STUDENT_USERNAME = os.getenv('DEMO_STUDENT_USERNAME', 'gosha')
DEMO_STUDENT_PASSWORD = os.getenv('DEMO_STUDENT_PASSWORD', 'gosha')
DEMO_STUDENT_NAME = os.getenv('DEMO_STUDENT_NAME', 'Гоша')

SEED_DATA_DIR = PROJECT_ROOT / 'data' / 'seeds'

# Legacy defaults used only to seed TelegramBotSettings on first load.
# Runtime config is stored in DB and edited via admin panel /api/telegram/settings
TELEGRAM_BOT_ENABLED = os.getenv('TELEGRAM_BOT_ENABLED', 'false').lower() in ('1', 'true', 'yes')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', '')
TELEGRAM_HTTP_PROXY = os.getenv('TELEGRAM_HTTP_PROXY', '').strip()
TELEGRAM_NOTIFY_ALL_SUBMISSIONS = os.getenv('TELEGRAM_NOTIFY_ALL_SUBMISSIONS', 'false').lower() in (
    '1', 'true', 'yes',
)

LOG_DIR = PROJECT_ROOT / 'logs'

from config.logging_setup import build_logging_config  # noqa: E402

LOGGING = build_logging_config(PROJECT_ROOT, debug=DEBUG)
