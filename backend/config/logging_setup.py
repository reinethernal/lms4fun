"""Central logging: daily rotation (TimedRotatingFileHandler) + restart rotation (rotate-logs.sh)."""
from __future__ import annotations

from pathlib import Path

LOG_STREAMS = ('django', 'celery', 'submissions', 'errors')
MAX_BACKUP_COUNT = 6  # 6 archived + 1 active = 7 files per stream


def log_dir(project_root: Path) -> Path:
    return project_root / 'logs'


def build_logging_config(project_root: Path, debug: bool = False) -> dict:
    directory = log_dir(project_root)
    directory.mkdir(parents=True, exist_ok=True)

    def rotating_handler(filename: str) -> dict:
        return {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(directory / filename),
            'when': 'midnight',
            'interval': 1,
            'backupCount': MAX_BACKUP_COUNT,
            'encoding': 'utf-8',
            'formatter': 'standard',
        }

    handlers = {
        'django_file': rotating_handler('django.log'),
        'celery_file': rotating_handler('celery.log'),
        'submissions_file': rotating_handler('submissions.log'),
        'errors_file': rotating_handler('errors.log'),
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    }

    console = ['console'] if debug else []

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': handlers,
        'root': {
            'handlers': ['django_file', *console],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['django_file', *console],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['errors_file', *console],
                'level': 'WARNING',
                'propagate': False,
            },
            'celery': {
                'handlers': ['celery_file', *console],
                'level': 'INFO',
                'propagate': False,
            },
            'apps.submissions': {
                'handlers': ['submissions_file', *console],
                'level': 'INFO',
                'propagate': False,
            },
            'apps.telegram': {
                'handlers': ['django_file', *console],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
