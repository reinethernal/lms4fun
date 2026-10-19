import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.gamification.models import Badge
from apps.tasks.models import Task


TASK_SLUG_BY_TITLE = {
    'Моя первая программа': 'print_hello',
    'Задание урока 2': 'game_profile',
    'Задание урока 5': 'points_calculator',
    'Задание урока 8': 'random_challenge',
    'Задание урока 10': 'guess_number_basic',
    'Задание урока 11': 'backpack_basic',
    'Задание урока 13': 'monster_catalog',
    'Задание урока 14': 'story_generator',
    'Задание урока 16': 'restore_energy_function',
    'Задание урока 19': 'challenge_round',
    'Задание урока 20': 'challenge_loop',
    'Задание урока 21': 'menu_basic',
    'Задание урока 22': 'shop_basic',
    'Задание урока 23': 'final_game',
}

TASK_TYPE_BY_SLUG = {
    'game_profile': Task.TaskType.PROJECT,
    'points_calculator': Task.TaskType.PROJECT,
    'guess_number_basic': Task.TaskType.PROJECT,
    'backpack_basic': Task.TaskType.PROJECT,
    'monster_catalog': Task.TaskType.PROJECT,
    'story_generator': Task.TaskType.PROJECT,
    'restore_energy_function': Task.TaskType.PROJECT,
    'challenge_round': Task.TaskType.CHALLENGE,
    'challenge_loop': Task.TaskType.CHALLENGE,
    'random_challenge': Task.TaskType.CHALLENGE,
    'menu_basic': Task.TaskType.PROJECT,
    'shop_basic': Task.TaskType.PROJECT,
    'final_game': Task.TaskType.PROJECT,
}


class Command(BaseCommand):
    help = 'Seed badges from badges_100.json and backfill task slugs for badge conditions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-slugs',
            action='store_true',
            help='Only seed badges, do not update task slugs.',
        )

    def handle(self, *args, **options):
        if not options['skip_slugs']:
            self._backfill_task_slugs()
        self._seed_badges()
        self.stdout.write(self.style.SUCCESS('Badge seed complete.'))

    def _backfill_task_slugs(self):
        updated = 0
        for title, slug in TASK_SLUG_BY_TITLE.items():
            tasks = Task.objects.filter(title=title)
            for task in tasks:
                changed = False
                if task.slug != slug:
                    if Task.objects.filter(lesson=task.lesson, slug=slug).exclude(pk=task.pk).exists():
                        base = slug
                        counter = 2
                        candidate = slug
                        while Task.objects.filter(lesson=task.lesson, slug=candidate).exclude(pk=task.pk).exists():
                            candidate = f'{base}-{counter}'
                            counter += 1
                        slug = candidate
                    task.slug = slug
                    changed = True
                task_type = TASK_TYPE_BY_SLUG.get(slug)
                if task_type and task.task_type != task_type:
                    task.task_type = task_type
                    changed = True
                if changed:
                    task.save(update_fields=['slug', 'task_type'])
                    updated += 1
        self.stdout.write(f'Updated {updated} task slugs/types')

    def _seed_badges(self):
        badges_file = Path(settings.SEED_DATA_DIR) / 'badges_100.json'
        if not badges_file.exists():
            self.stdout.write(self.style.WARNING(f'No badges file at {badges_file}'))
            return

        data = json.loads(badges_file.read_text(encoding='utf-8'))
        created = 0
        for item in data:
            title = item['title']
            defaults = {
                'description': item.get('description', ''),
                'icon': item.get('icon', ''),
                'badge_type': item.get('badge_type', Badge.BadgeType.ACHIEVEMENT),
                'level': item.get('level', Badge.BadgeLevel.BRONZE),
                'condition_key': item.get('condition_key', ''),
                'condition_value': item.get('condition_value'),
                'condition_params': item.get('condition_params') or {},
                'is_active': item.get('is_active', True),
            }
            _, was_created = Badge.objects.get_or_create(title=title, defaults=defaults)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} new badges ({Badge.objects.count()} total)'))
