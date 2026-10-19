"""Re-check accepted submissions: auto-checker where possible, else manual_review."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.courses.models import Course
from apps.submissions.models import Submission
from apps.submissions.starter_guard import should_reject_unchanged_starter
from apps.tasks.demo import is_run_only_task
from apps.tasks.models import Task


class Command(BaseCommand):
    help = (
        'Re-check accepted submissions. Tasks with auto checkers go to pending+Judge0; '
        'manual tasks go to manual_review.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--course-slug', default='python-starter')
        parser.add_argument('--from-lesson', type=int, default=1)
        parser.add_argument('--to-lesson', type=int, default=999)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--notify', action='store_true', help='Send telegram notifications after enqueue')
        parser.add_argument(
            '--only-unchanged-starter',
            action='store_true',
            help='Only process submissions whose code matches the task starter',
        )
        parser.add_argument(
            '--statuses',
            default='accepted,manual_review',
            help='Comma-separated statuses to pick up (default: accepted,manual_review)',
        )

    def handle(self, *args, **options):
        course_slug = options['course_slug']
        from_lesson = options['from_lesson']
        to_lesson = options['to_lesson']
        dry_run = options['dry_run']
        notify = options['notify']
        only_starter = options['only_unchanged_starter']
        statuses = [s.strip() for s in options['statuses'].split(',') if s.strip()]

        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Course not found: {course_slug}'))
            return

        lessons = course.lessons.filter(number__gte=from_lesson, number__lte=to_lesson)
        task_ids = []
        for lesson in lessons.prefetch_related('tasks'):
            for task in lesson.tasks.all():
                if is_run_only_task(task):
                    continue
                if not task.is_required:
                    continue
                task_ids.append(task.id)

        qs = (
            Submission.objects.filter(
                task_id__in=task_ids,
                status__in=statuses,
            )
            .select_related('task', 'task__lesson', 'user')
            .order_by('id')
        )

        to_process = []
        for sub in qs:
            if only_starter and not should_reject_unchanged_starter(sub.task, sub.code, sub.user):
                continue
            to_process.append(sub)

        self.stdout.write(
            f'Found {len(to_process)} submission(s) for lessons {from_lesson}–{to_lesson} '
            f'(statuses={statuses})'
        )
        if dry_run:
            for sub in to_process[:50]:
                mode = 'auto' if sub.task.checker_type != Task.CheckerType.MANUAL else 'manual'
                self.stdout.write(
                    f'Would recheck #{sub.id} [{mode}] {sub.user} / '
                    f'L{sub.task.lesson.number} {sub.task.title}'
                )
            self.stdout.write(self.style.WARNING('Dry run complete'))
            return

        from apps.submissions.tasks import check_submission_task

        updated_ids = []
        auto_ids = []
        manual_ids = []
        for sub in to_process:
            if sub.task.checker_type == Task.CheckerType.MANUAL:
                sub.status = Submission.Status.MANUAL_REVIEW
                sub.checked_at = None
                sub.checked_by = None
                sub.score = 0
                sub.checker_result = {
                    'requeued_at': timezone.now().isoformat(),
                    'reason': 'manual_task_requeue',
                }
                sub.save(update_fields=[
                    'status', 'checked_at', 'checked_by', 'score', 'checker_result',
                ])
                manual_ids.append(sub.id)
            else:
                sub.status = Submission.Status.PENDING
                sub.checked_at = None
                sub.checked_by = None
                sub.score = 0
                sub.xp_awarded = 0
                sub.checker_result = {
                    'requeued_at': timezone.now().isoformat(),
                    'reason': 'auto_recheck',
                }
                sub.save(update_fields=[
                    'status', 'checked_at', 'checked_by', 'score', 'xp_awarded', 'checker_result',
                ])
                check_submission_task.delay(sub.id)
                auto_ids.append(sub.id)
            updated_ids.append(sub.id)
            self.stdout.write(
                f'Requeued #{sub.id} '
                f'{"auto" if sub.id in auto_ids else "manual"} '
                f'{sub.user} / L{sub.task.lesson.number} {sub.task.title}'
            )

        if notify and updated_ids:
            try:
                from apps.telegram.tasks import notify_staff_submission_task
            except ImportError:
                notify_staff_submission_task = None
            if notify_staff_submission_task is not None:
                # Notify after auto-check completes via check_submission_task;
                # for manual-only, notify now.
                for sid in manual_ids:
                    notify_staff_submission_task.delay(sid)
                self.stdout.write(f'Queued {len(manual_ids)} telegram notifications (manual)')
            else:
                self.stderr.write('Telegram notify task unavailable')

        self.stdout.write(self.style.SUCCESS(
            f'Done: {len(auto_ids)} auto-recheck, {len(manual_ids)} manual_review'
        ))
