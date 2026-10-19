import json

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsPlatformAdmin, IsStaffMember
from apps.notifications.services import log_audit

from .models import ImportJob
from .serializers import ImportJobSerializer
from .services import export_course, export_leaderboard, run_import_job


def _course_payload(data: dict) -> dict:
    return {'data': data.get('data', data)}


def _lesson_payload(data: dict) -> dict:
    payload: dict = {}
    if data.get('course_id'):
        payload['course_id'] = int(data['course_id'])
    if data.get('markdown'):
        payload['markdown'] = data['markdown']
    else:
        payload['data'] = data.get('data', data)
    return payload


def _tasks_payload(data: dict) -> dict:
    lesson_id = data.get('lesson_id')
    if not lesson_id:
        inner = data.get('data', data)
        if isinstance(inner, dict):
            lesson_id = inner.get('lesson_id')
    if not lesson_id:
        raise ValueError('Укажите lesson_id.')
    inner = data.get('data', data)
    tasks = data.get('tasks')
    if tasks is None and isinstance(inner, dict):
        tasks = inner.get('tasks', inner)
    else:
        tasks = tasks or inner
    return {'lesson_id': int(lesson_id), 'data': tasks}


def _build_payload(request, import_type: str) -> dict:
    if request.FILES.get('file'):
        uploaded = request.FILES['file']
        name = uploaded.name.lower()
        if name.endswith('.zip'):
            return {'zip_bytes': uploaded.read()}
        if name.endswith('.md'):
            payload = {'markdown': uploaded.read().decode('utf-8')}
            if request.data.get('course_id'):
                payload['course_id'] = int(request.data['course_id'])
            return payload
        return {'data': json.loads(uploaded.read().decode('utf-8'))}

    data = dict(request.data)
    if import_type == ImportJob.ImportType.TASKS:
        return _tasks_payload(data)
    if import_type == ImportJob.ImportType.LESSON:
        return _lesson_payload(data)
    return _course_payload(data)


class _ImportBaseView(APIView):
    permission_classes = [IsStaffMember]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    import_type = ''
    audit_action = ''

    def post(self, request):
        file_name = 'import.json'
        if request.FILES.get('file'):
            file_name = request.FILES['file'].name
        elif isinstance(request.data, dict) and request.data.get('slug'):
            file_name = f"{request.data['slug']}.json"

        job = ImportJob.objects.create(
            user=request.user,
            import_type=self.import_type,
            file_name=file_name,
        )
        try:
            payload = _build_payload(request, self.import_type)
            run_import_job(job, payload)
        except Exception as exc:
            job.status = ImportJob.Status.FAILED
            job.errors_json = [str(exc)]
            job.finished_at = timezone.now()
            job.save(update_fields=['status', 'errors_json', 'finished_at'])

        log_audit(request.user, self.audit_action, 'import_job', job.id, {'status': job.status}, request)

        code = status.HTTP_201_CREATED
        if job.status == ImportJob.Status.FAILED:
            code = status.HTTP_400_BAD_REQUEST
        return Response(ImportJobSerializer(job).data, status=code)


class ImportCourseView(_ImportBaseView):
    import_type = ImportJob.ImportType.COURSE
    audit_action = 'import.course'


class ImportLessonView(_ImportBaseView):
    import_type = ImportJob.ImportType.LESSON
    audit_action = 'import.lesson'


class ImportTasksView(_ImportBaseView):
    import_type = ImportJob.ImportType.TASKS
    audit_action = 'import.tasks'


class ImportJobListView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        jobs = ImportJob.objects.all().order_by('-created_at')[:100]
        if not request.user.is_platform_admin:
            jobs = jobs.filter(user=request.user)
        return Response(ImportJobSerializer(jobs, many=True).data)


class ExportCourseView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request, pk):
        data = export_course(pk)
        log_audit(request.user, 'export.course', 'course', pk, {}, request)
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8',
        )
        response['Content-Disposition'] = f'attachment; filename="course_{pk}.json"'
        return response


class ExportLeaderboardView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        course_id = request.query_params.get('course_id')
        group_id = request.query_params.get('group_id')
        data = export_leaderboard(course_id=course_id, group_id=group_id)
        log_audit(request.user, 'export.leaderboard', 'leaderboard', '', {}, request)
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8',
        )
        response['Content-Disposition'] = f'attachment; filename="leaderboard_{timezone.now():%Y%m%d}.json"'
        return response
