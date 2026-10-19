from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.submissions.models import Submission
from apps.submissions.serializers import AdminSubmissionListSerializer

from .models import User
from .profile import can_view_student_profile


class StudentSubmissionsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            student = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if not can_view_student_profile(request.user, student):
            return Response({'detail': 'Нет доступа.'}, status=status.HTTP_403_FORBIDDEN)

        submissions = (
            Submission.objects.filter(user=student)
            .select_related('user', 'task', 'task__lesson', 'language')
            .order_by('-submitted_at')
        )

        task_id = request.query_params.get('task_id')
        if task_id:
            submissions = submissions.filter(task_id=task_id)

        return Response(AdminSubmissionListSerializer(submissions[:200], many=True).data)
