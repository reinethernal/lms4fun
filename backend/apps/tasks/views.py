from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffMember
from apps.courses.views import _accessible_courses

from .models import Task
from .personalize import personalize_text
from .serializers import TaskDetailSerializer, TaskListSerializer, TaskWriteSerializer


class LessonTasksView(APIView):
    def get(self, request, pk):
        from apps.lessons.models import Lesson
        from apps.lessons.progress import is_lesson_locked_for_user

        lesson = Lesson.objects.select_related('course').get(pk=pk, status='published')
        if not _accessible_courses(request.user).filter(pk=lesson.course_id).exists():
            return Response({'detail': 'Нет доступа.'}, status=status.HTTP_403_FORBIDDEN)
        if is_lesson_locked_for_user(request.user, lesson):
            return Response(
                {
                    'detail': 'Сначала пройдите предыдущий урок.',
                    'is_locked': True,
                    'course_id': lesson.course_id,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        tasks = Task.objects.filter(lesson=lesson)
        data = TaskListSerializer(tasks, many=True, context={'request': request}).data
        for item in data:
            item['starter_code'] = personalize_text(item.get('starter_code', ''), request.user)
            item['description'] = personalize_text(item.get('description', ''), request.user)
        return Response(data)


class AdminTaskListCreateView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        lesson_id = request.query_params.get('lesson_id')
        tasks = Task.objects.select_related('lesson', 'language').all()
        if lesson_id:
            tasks = tasks.filter(lesson_id=lesson_id)
        return Response(TaskWriteSerializer(tasks, many=True).data)

    def post(self, request):
        serializer = TaskWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskWriteSerializer(task).data, status=status.HTTP_201_CREATED)


class AdminTaskDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get_object(self, pk):
        return Task.objects.select_related('lesson', 'language').get(pk=pk)

    def get(self, request, pk):
        task = self.get_object(pk)
        return Response(TaskWriteSerializer(task).data)

    def patch(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskWriteSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskWriteSerializer(task).data)

    def delete(self, request, pk):
        task = self.get_object(pk)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
