from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.parent_access import can_view_submission
from apps.accounts.permissions import IsStaffMember, IsStudentOrStaff
from apps.courses.models import ProgrammingLanguage
from apps.tasks.demo import is_run_only_task
from apps.tasks.models import Task

from .error_explainer import (
    explain_execution_error,
    explain_stdin_validation,
    guidance_summary,
    is_waiting_for_input,
)
from .judge0_client import Judge0Client, normalize_judge0_result
from .models import CodeRun, Submission
from .serializers import (
    AdminSubmissionDetailSerializer,
    AdminSubmissionListSerializer,
    CodeRunRequestSerializer,
    SubmissionCreateSerializer,
    SubmissionResponseSerializer,
    SubmissionReviewSerializer,
    SubmissionSerializer,
)
from .access import get_staff_submission, submissions_queryset_for_staff
from .review import review_submission
from .starter_guard import should_reject_unchanged_starter
from .tasks import check_submission_task


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class CodeRunView(APIView):
    permission_classes = [IsStudentOrStaff]

    def post(self, request):
        serializer = CodeRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            language = ProgrammingLanguage.objects.get(slug=data['language'], is_active=True)
        except ProgrammingLanguage.DoesNotExist:
            return Response({'detail': 'Язык не найден.'}, status=status.HTTP_400_BAD_REQUEST)

        source_code = data['source_code']
        stdin = data.get('stdin', '')
        repl_mode = data.get('repl_mode', False)
        if not repl_mode:
            stdin_guidance = explain_stdin_validation(source_code, stdin)
            if stdin_guidance:
                return Response(
                    {
                        'detail': guidance_summary(stdin_guidance),
                        'error_guidance': stdin_guidance,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        client = Judge0Client()
        try:
            raw = client.run_code(
                data['source_code'],
                language.judge0_language_id,
                data.get('stdin', ''),
                language.default_time_limit,
                language.default_memory_limit,
            )
            normalized = normalize_judge0_result(raw)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        lesson = None
        task = None
        course = None
        if data.get('lesson_id'):
            from apps.lessons.models import Lesson
            lesson = Lesson.objects.filter(pk=data['lesson_id']).first()
            if lesson:
                course = lesson.course
        if data.get('task_id'):
            task = Task.objects.filter(pk=data['task_id']).select_related(
                'lesson',
                'lesson__course',
                'lesson__course__primary_language',
                'lesson__language',
                'language',
            ).first()
            if task and not lesson:
                lesson = task.lesson
                course = lesson.course
            if task:
                required_lang = task.language
                if task.lesson.course.primary_language_id:
                    required_lang = task.lesson.course.primary_language
                elif task.lesson.language_id:
                    required_lang = task.lesson.language
                if data['language'] != required_lang.slug:
                    return Response(
                        {
                            'detail': f'Для этого задания доступен только {required_lang.name}.',
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        if lesson and request.user.is_student:
            from apps.lessons.progress import is_lesson_locked_for_user
            if is_lesson_locked_for_user(request.user, lesson):
                return Response(
                    {
                        'detail': 'Сначала пройдите предыдущий урок.',
                        'is_locked': True,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        code_run = CodeRun.objects.create(
            user=request.user,
            course=course,
            lesson=lesson,
            task=task,
            language=language,
            source_code=data['source_code'],
            stdin=data.get('stdin', ''),
            stdout=normalized['stdout'],
            stderr=normalized['stderr'],
            compile_output=normalized['compile_output'],
            exit_code=normalized.get('exit_code'),
            execution_time=normalized['execution_time'],
            memory_used=normalized['memory_used'],
            status=normalized['status'],
            ip_address=_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        new_badges = []
        from apps.gamification.stats import serialize_awarded_badges, update_stats_on_code_run

        if normalized['status'] == 'success':
            new_badges = update_stats_on_code_run(request.user, code_run)

        waiting_for_input = repl_mode and is_waiting_for_input(
            source_code=source_code,
            stdin=stdin,
            run_status=normalized['status'],
            stderr=normalized.get('stderr', ''),
        )
        response_status = 'waiting_input' if waiting_for_input else normalized['status']

        response_data = {
            'status': response_status,
            'language': language.slug,
            'stdout': normalized['stdout'],
            'stderr': normalized['stderr'],
            'compile_output': normalized['compile_output'],
            'execution_time': normalized['execution_time'],
            'memory_used': normalized['memory_used'],
            'new_badges': serialize_awarded_badges(new_badges, request),
        }
        if waiting_for_input:
            response_data['waiting_for_input'] = True
        elif normalized['status'] != 'success':
            response_data['error_guidance'] = explain_execution_error(
                normalized.get('stderr', ''),
                normalized.get('compile_output', ''),
                source_code=data['source_code'],
                stdin=data.get('stdin', ''),
                language=language.slug,
                status=normalized['status'],
                is_trial_run=True,
            )
        return Response(response_data)


class SubmissionCreateView(APIView):
    permission_classes = [IsStudentOrStaff]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            task = Task.objects.select_related('language', 'lesson', 'lesson__course').get(pk=data['task_id'])
        except Task.DoesNotExist:
            return Response({'detail': 'Задание не найдено.'}, status=status.HTTP_404_NOT_FOUND)

        from apps.lessons.progress import is_lesson_locked_for_user

        if is_lesson_locked_for_user(request.user, task.lesson):
            return Response(
                {
                    'detail': 'Сначала пройдите предыдущий урок.',
                    'is_locked': True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if is_run_only_task(task):
            return Response(
                {
                    'detail': 'Это демо-задание: его нужно только запустить, сдавать не нужно.',
                    'run_only': True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if should_reject_unchanged_starter(task, data['source_code'], request.user):
            return Response(
                {
                    'detail': 'Сначала измени код задания. Нельзя сдавать стартовый код без изменений.',
                    'unchanged_starter': True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission = Submission.objects.create(
            user=request.user,
            task=task,
            language=task.language,
            code=data['source_code'],
            status=Submission.Status.PENDING,
        )

        check_submission_task.delay(submission.id)

        return Response({
            'id': submission.id,
            'status': 'pending',
            'xp_awarded': 0,
            'message': 'Решение отправлено на проверку.',
        }, status=status.HTTP_202_ACCEPTED)


class SubmissionDetailView(APIView):
    def get(self, request, pk):
        submission = Submission.objects.select_related('task', 'language', 'user').get(pk=pk)
        if not can_view_submission(request.user, submission):
            return Response({'detail': 'Нет доступа.'}, status=status.HTTP_403_FORBIDDEN)

        if (
            request.user.is_platform_admin
            or request.user.is_teacher
            or request.user.is_parent
            or submission.user_id == request.user.id
        ):
            return Response(AdminSubmissionDetailSerializer(submission).data)

        if submission.status == Submission.Status.PENDING:
            return Response(SubmissionSerializer(submission).data)

        checker = submission.checker_result or {}
        payload = {
            'status': submission.status,
            'xp_awarded': submission.xp_awarded,
            'message': checker.get('message', ''),
            'new_badges': checker.get('new_badges', []),
        }
        for key in ('failed_test_index', 'expected', 'got', 'is_hidden'):
            if key in checker:
                payload[key] = checker[key]
        return Response(SubmissionResponseSerializer(payload).data)


class MySubmissionsListView(APIView):
    permission_classes = [IsStudentOrStaff]

    def get(self, request):
        submissions = (
            Submission.objects.filter(user=request.user)
            .select_related('user', 'task', 'language')
            .order_by('-submitted_at')[:200]
        )
        return Response(AdminSubmissionListSerializer(submissions, many=True).data)


def _submissions_for_staff(user, request=None):
    return submissions_queryset_for_staff(user, request)


def _get_staff_submission(user, pk):
    return get_staff_submission(user, pk)


class AdminSubmissionListView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        submissions = _submissions_for_staff(request.user, request)[:200]
        return Response(AdminSubmissionListSerializer(submissions, many=True).data)


class AdminSubmissionDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request, pk):
        submission = _get_staff_submission(request.user, pk)
        if submission is None:
            return Response({'detail': 'Решение не найдено.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminSubmissionDetailSerializer(submission).data)

    def patch(self, request, pk):
        submission = _get_staff_submission(request.user, pk)
        if submission is None:
            return Response({'detail': 'Решение не найдено.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SubmissionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            submission = review_submission(
                submission,
                request.user,
                status=data['status'],
                teacher_comment=data.get('teacher_comment', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AdminSubmissionDetailSerializer(submission).data)


class AdminSubmissionRecheckView(APIView):
    permission_classes = [IsStaffMember]

    def post(self, request, pk):
        submission = _get_staff_submission(request.user, pk)
        if submission is None:
            return Response({'detail': 'Решение не найдено.'}, status=status.HTTP_404_NOT_FOUND)

        if submission.status in (Submission.Status.PENDING, Submission.Status.RUNNING):
            return Response({'detail': 'Проверка уже выполняется.'}, status=status.HTTP_400_BAD_REQUEST)

        submission.status = Submission.Status.PENDING
        submission.checked_at = None
        submission.checked_by = None
        submission.save(update_fields=['status', 'checked_at', 'checked_by'])
        check_submission_task.delay(submission.id)

        return Response({
            'id': submission.id,
            'status': 'pending',
            'message': 'Решение отправлено на повторную проверку.',
        }, status=status.HTTP_202_ACCEPTED)
