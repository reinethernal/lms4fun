from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffMember
from apps.courses.models import Course
from apps.courses.views import _accessible_courses

from .models import Lesson
from .progress import is_lesson_locked_for_user
from .serializers import LessonDetailSerializer, LessonListSerializer, LessonWriteSerializer


class CourseLessonsView(APIView):
    def get(self, request, pk):
        course = _accessible_courses(request.user).get(pk=pk)
        lessons = Lesson.objects.filter(
            course=course,
            status=Lesson.Status.PUBLISHED,
        ).order_by('sort_order', 'number', 'id')
        return Response(
            LessonListSerializer(
                lessons,
                many=True,
                context={'request': request, 'course': course},
            ).data,
        )


class LessonDetailView(APIView):
    def get(self, request, pk):
        lesson = Lesson.objects.select_related('course', 'language').get(
            pk=pk,
            status=Lesson.Status.PUBLISHED,
        )
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
        from apps.tasks.personalize import personalize_text

        data = LessonDetailSerializer(lesson).data
        for field in (
            'goal', 'theory_text', 'simple_explanation', 'practice_text',
            'mini_project_text', 'summary_text',
        ):
            if data.get(field):
                data[field] = personalize_text(data[field], request.user)
        return Response(data)


class AdminLessonListCreateView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        course_id = request.query_params.get('course_id')
        lessons = Lesson.objects.select_related('course', 'language').all()
        if course_id:
            lessons = lessons.filter(course_id=course_id)
        return Response(LessonDetailSerializer(lessons, many=True).data)

    def post(self, request):
        serializer = LessonWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        return Response(LessonDetailSerializer(lesson).data, status=status.HTTP_201_CREATED)


class AdminLessonDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get_object(self, pk):
        return Lesson.objects.select_related('course', 'language').get(pk=pk)

    def get(self, request, pk):
        lesson = self.get_object(pk)
        return Response(LessonDetailSerializer(lesson).data)

    def patch(self, request, pk):
        lesson = self.get_object(pk)
        serializer = LessonWriteSerializer(lesson, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        return Response(LessonDetailSerializer(lesson).data)

    def delete(self, request, pk):
        lesson = self.get_object(pk)
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
