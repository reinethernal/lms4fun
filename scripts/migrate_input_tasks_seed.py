#!/usr/bin/env python3
"""Migrate input() tasks in python_starter_course.json to stdin_stdout checker."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / 'data' / 'seeds' / 'python_starter_course.json'

TASK_TESTS: dict[str, dict] = {
    'print_hello': {
        'starter_code': (
            'student_name = input("Как тебя зовут? ")\n'
            'print(f"Привет! Я {student_name}!")\n'
        ),
        'visible_tests_json': [
            {'stdin': 'Гоша', 'expected_stdout': 'Привет! Я Гоша!'},
            {'stdin': 'Аня', 'expected_stdout': 'Привет! Я Аня!'},
        ],
        'hidden_tests_json': [
            {'stdin': 'Тест', 'expected_stdout': 'Привет! Я Тест!', 'hidden': True},
        ],
    },
    'lesson-4:1': {
        'visible_tests_json': [
            {'stdin': 'Гоша', 'expected_stdout': 'Привет, Гоша!'},
        ],
        'hidden_tests_json': [
            {'stdin': 'Маша', 'expected_stdout': 'Привет, Маша!', 'hidden': True},
        ],
    },
    'lesson-4:2': {
        'visible_tests_json': [
            {'stdin': 'Гоша', 'expected_stdout': 'Привет, Гоша!'},
        ],
        'hidden_tests_json': [
            {'stdin': 'Петя', 'expected_stdout': 'Привет, Петя!', 'hidden': True},
        ],
    },
    'lesson-5:1': {
        'visible_tests_json': [{'stdin': '10', 'expected_stdout': '11'}],
        'hidden_tests_json': [{'stdin': '0', 'expected_stdout': '1', 'hidden': True}],
    },
    'points_calculator': {
        'visible_tests_json': [{'stdin': '10', 'expected_stdout': '11'}],
        'hidden_tests_json': [
            {'stdin': '5', 'expected_stdout': '6', 'hidden': True},
            {'stdin': '100', 'expected_stdout': '101', 'hidden': True},
        ],
    },
    'lesson-6:1': {
        'visible_tests_json': [
            {'stdin': '5', 'expected_stdout': 'положительное'},
            {'stdin': '-1', 'expected_stdout': 'не положительное'},
        ],
        'hidden_tests_json': [
            {'stdin': '0', 'expected_stdout': 'не положительное', 'hidden': True},
        ],
    },
    'lesson-6:2': {
        'visible_tests_json': [
            {'stdin': '5', 'expected_stdout': 'положительное'},
            {'stdin': '-1', 'expected_stdout': 'не положительное'},
        ],
        'hidden_tests_json': [
            {'stdin': '0', 'expected_stdout': 'не положительное', 'hidden': True},
        ],
    },
    'lesson-7:1': {
        'visible_tests_json': [
            {'stdin': '15', 'expected_stdout': 'большое'},
            {'stdin': '5', 'expected_stdout': 'маленькое'},
            {'stdin': '-3', 'expected_stdout': 'отрицательное'},
        ],
        'hidden_tests_json': [
            {'stdin': '0', 'expected_stdout': 'отрицательное', 'hidden': True},
        ],
    },
    'lesson-7:2': {
        'visible_tests_json': [
            {'stdin': '15', 'expected_stdout': 'большое'},
            {'stdin': '5', 'expected_stdout': 'маленькое'},
        ],
        'hidden_tests_json': [
            {'stdin': '-1', 'expected_stdout': 'отрицательное', 'hidden': True},
        ],
    },
    'guess_number_basic': {
        'starter_code': (
            'secret = 7  # фиксировано для автопроверки\n'
            'guess = int(input())\n'
            'if guess == secret:\n'
            '    print("Верно!")\n'
            'elif guess < secret:\n'
            '    print("Больше")\n'
            'else:\n'
            '    print("Меньше")\n'
        ),
        'visible_tests_json': [
            {'stdin': '7', 'expected_stdout': 'Верно!'},
            {'stdin': '3', 'expected_stdout': 'Больше'},
        ],
        'hidden_tests_json': [
            {'stdin': '10', 'expected_stdout': 'Меньше', 'hidden': True},
        ],
    },
    'lesson-14:1': {
        'visible_tests_json': [
            {'stdin': 'рыцарь\nлес', 'expected_stdout': 'рыцарь пошёл в лес'},
        ],
        'hidden_tests_json': [
            {'stdin': 'маг\nзамок', 'expected_stdout': 'маг пошёл в замок', 'hidden': True},
        ],
    },
    'story_generator': {
        'visible_tests_json': [
            {'stdin': 'Герой\nгород', 'expected_stdout': 'Герой пошёл в город'},
        ],
        'hidden_tests_json': [
            {'stdin': 'Волк\nлес', 'expected_stdout': 'Волк пошёл в лес', 'hidden': True},
        ],
    },
    'lesson-19:1': {
        'visible_tests_json': [
            {'stdin': '4', 'expected_stdout': '1'},
            {'stdin': '5', 'expected_stdout': '0'},
        ],
        'hidden_tests_json': [
            {'stdin': '4', 'expected_stdout': '1', 'hidden': True},
        ],
    },
    'challenge_round': {
        'visible_tests_json': [{'stdin': '4', 'expected_stdout': '1'}],
        'hidden_tests_json': [{'stdin': '3', 'expected_stdout': '0', 'hidden': True}],
    },
    'lesson-20:1': {
        'visible_tests_json': [{'stdin': 'да\nнет\nда', 'expected_stdout': '2'}],
        'hidden_tests_json': [
            {'stdin': 'нет\nнет\nнет', 'expected_stdout': '0', 'hidden': True},
        ],
    },
    'challenge_loop': {
        'visible_tests_json': [{'stdin': 'да\nда\nда', 'expected_stdout': '3'}],
        'hidden_tests_json': [
            {'stdin': 'да\nнет\nда', 'expected_stdout': '2', 'hidden': True},
        ],
    },
    'lesson-21:1': {
        'visible_tests_json': [
            {'stdin': '1', 'expected_stdout': 'старт'},
            {'stdin': '2', 'expected_stdout': 'выход'},
        ],
        'hidden_tests_json': [
            {'stdin': '1', 'expected_stdout': 'старт', 'hidden': True},
        ],
    },
    'menu_basic': {
        'visible_tests_json': [
            {'stdin': '1', 'expected_stdout': 'старт'},
            {'stdin': '2', 'expected_stdout': 'выход'},
        ],
        'hidden_tests_json': [
            {'stdin': '2', 'expected_stdout': 'выход', 'hidden': True},
        ],
    },
}


def task_key(lesson_slug: str, task: dict) -> str:
    if task.get('slug'):
        return task['slug']
    return f"{lesson_slug}:{task.get('sort_order', 0)}"


def has_input(starter: str) -> bool:
    return bool(re.search(r'\binput\s*\(', starter or ''))


def apply_stdin_migration(task: dict, key: str) -> bool:
    if not has_input(task.get('starter_code', '')):
        return False
    if key == 'lesson-10:1':
        return False
    config = TASK_TESTS.get(key)
    if not config:
        return False
    task['checker_type'] = 'stdin_stdout'
    task.pop('expected_output', None)
    task.pop('stdin', None)
    task['checker_config_json'] = {}
    if 'starter_code' in config:
        task['starter_code'] = config['starter_code']
    if 'visible_tests_json' in config:
        task['visible_tests_json'] = config['visible_tests_json']
    if 'hidden_tests_json' in config:
        task['hidden_tests_json'] = config['hidden_tests_json']
    return True


def main() -> None:
    data = json.loads(SEED_PATH.read_text(encoding='utf-8'))
    migrated = 0
    for lesson in data.get('lessons', []):
        slug = lesson.get('slug', '')
        for task in lesson.get('tasks', []):
            key = task_key(slug, task)
            if apply_stdin_migration(task, key):
                migrated += 1
                print(f'  migrated {key}')
    SEED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Migrated {migrated} input tasks')


if __name__ == '__main__':
    main()
