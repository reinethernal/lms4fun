import base64
import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_B64_FIELDS = (
    'source_code',
    'stdin',
    'stdout',
    'stderr',
    'compile_output',
    'expected_output',
    'message',
)


class Judge0Error(Exception):
    pass


def _b64_encode(value: str) -> str:
    return base64.b64encode(value.encode('utf-8')).decode('ascii')


def _decode_submission_fields(result: dict[str, Any]) -> dict[str, Any]:
    decoded = dict(result)
    for field in _B64_FIELDS:
        raw = decoded.get(field)
        if not raw or not isinstance(raw, str):
            continue
        try:
            decoded[field] = base64.b64decode(raw).decode('utf-8', errors='replace')
        except Exception:
            logger.warning('Failed to base64-decode Judge0 field %s', field)
    return decoded


class Judge0Client:
    """Client for Judge0 CE submissions API."""

    def __init__(self):
        self.base_url = settings.JUDGE0_API_URL.rstrip('/')
        self.token = settings.JUDGE0_API_TOKEN
        self.default_time_limit = settings.CODE_RUN_TIME_LIMIT
        self.default_memory_limit = settings.CODE_RUN_MEMORY_LIMIT

    def _headers(self) -> dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['X-Auth-Token'] = self.token
        return headers

    def _params(self, **extra: str) -> dict[str, str]:
        return {'base64_encoded': 'true', **extra}

    def create_submission(
        self,
        source_code: str,
        language_id: int,
        stdin: str = '',
        time_limit: float | None = None,
        memory_limit: int | None = None,
    ) -> str:
        payload = {
            'source_code': _b64_encode(source_code),
            'language_id': language_id,
            'stdin': _b64_encode(stdin or ''),
            'cpu_time_limit': time_limit or self.default_time_limit,
            'memory_limit': memory_limit or self.default_memory_limit,
        }
        response = requests.post(
            f'{self.base_url}/submissions',
            json=payload,
            headers=self._headers(),
            params=self._params(wait='false'),
            timeout=30,
        )
        if response.status_code not in (200, 201):
            logger.error('Judge0 create failed: %s %s', response.status_code, response.text)
            raise Judge0Error(f'Judge0 create failed: {response.status_code}')
        return response.json()['token']

    def get_submission(self, token: str) -> dict[str, Any]:
        response = requests.get(
            f'{self.base_url}/submissions/{token}',
            headers=self._headers(),
            params=self._params(fields='*'),
            timeout=30,
        )
        if response.status_code != 200:
            logger.error('Judge0 get failed: %s %s', response.status_code, response.text)
            raise Judge0Error(f'Judge0 get failed: {response.status_code}')
        return _decode_submission_fields(response.json())

    def wait_for_result(
        self,
        token: str,
        poll_interval: float = 0.3,
        max_wait: float = 30.0,
    ) -> dict[str, Any]:
        deadline = time.time() + max_wait
        while time.time() < deadline:
            result = self.get_submission(token)
            status_id = result.get('status', {}).get('id')
            # 1=In Queue, 2=Processing
            if status_id not in (1, 2):
                return result
            time.sleep(poll_interval)
        raise Judge0Error('Judge0 execution timed out')

    def run_code(
        self,
        source_code: str,
        language_id: int,
        stdin: str = '',
        time_limit: float | None = None,
        memory_limit: int | None = None,
    ) -> dict[str, Any]:
        token = self.create_submission(source_code, language_id, stdin, time_limit, memory_limit)
        return self.wait_for_result(token)


def normalize_judge0_result(result: dict[str, Any]) -> dict[str, Any]:
    status_desc = result.get('status', {}).get('description', '')
    status_id = result.get('status', {}).get('id', 0)
    if status_id == 3:
        status = 'success'
    elif status_id in (5, 6):
        status = 'compile_error'
    elif status_id in (7, 8, 9, 10, 11, 12):
        status = 'error'
    elif status_id == 13:
        status = 'timeout'
    else:
        status = 'error'
    return {
        'status': status,
        'stdout': result.get('stdout') or '',
        'stderr': result.get('stderr') or '',
        'compile_output': result.get('compile_output') or '',
        'execution_time': float(result.get('time') or 0),
        'memory_used': int(result.get('memory') or 0),
        'exit_code': result.get('exit_code'),
        'judge0_status': status_desc,
    }
