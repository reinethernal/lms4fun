from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsPlatformAdmin, IsStaffMember

from .models import Course, CourseAssignment, ProgrammingLanguage
from .serializers import (
    CourseAssignmentSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseWriteSerializer,
    ProgrammingLanguageSerializer,
)


def _accessible_courses(user):
    if user.is_platform_admin or user.is_teacher:
        return Course.objects.filter(status=Course.Status.PUBLISHED)
    if user.is_parent:
        child_ids = user.children.values_list('id', flat=True)
        assigned = CourseAssignment.objects.filter(
            Q(user_id__in=child_ids) | Q(group__memberships__user_id__in=child_ids),
            status=CourseAssignment.Status.ACTIVE,
        ).values_list('course_id', flat=True)
        return Course.objects.filter(id__in=assigned, status=Course.Status.PUBLISHED).distinct()
    assigned = CourseAssignment.objects.filter(
        Q(user=user) | Q(group__memberships__user=user),
        status=CourseAssignment.Status.ACTIVE,
    ).values_list('course_id', flat=True)
    return Course.objects.filter(
        Q(id__in=assigned) | Q(visibility=Course.Visibility.PUBLIC),
        status=Course.Status.PUBLISHED,
    ).distinct()


class LanguageListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        languages = ProgrammingLanguage.objects.filter(is_active=True)
        return Response(ProgrammingLanguageSerializer(languages, many=True).data)


class CourseListView(APIView):
    def get(self, request):
        courses = _accessible_courses(request.user)
        return Response(CourseListSerializer(courses, many=True).data)


class CourseDetailView(APIView):
    def get(self, request, pk):
        course = _accessible_courses(request.user).get(pk=pk)
        return Response(CourseDetailSerializer(course).data)


class AdminCourseListCreateView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        courses = Course.objects.select_related('primary_language', 'author').all()
        return Response(CourseDetailSerializer(courses, many=True).data)

    def post(self, request):
        serializer = CourseWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        return Response(CourseDetailSerializer(course).data, status=status.HTTP_201_CREATED)


class AdminCourseDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get_object(self, pk):
        return Course.objects.select_related('primary_language', 'author').get(pk=pk)

    def get(self, request, pk):
        course = self.get_object(pk)
        return Response(CourseDetailSerializer(course).data)

    def patch(self, request, pk):
        course = self.get_object(pk)
        serializer = CourseWriteSerializer(course, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        return Response(CourseDetailSerializer(course).data)

    def delete(self, request, pk):
        course = self.get_object(pk)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminLanguageListCreateView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        languages = ProgrammingLanguage.objects.all()
        return Response(ProgrammingLanguageSerializer(languages, many=True).data)

    def post(self, request):
        serializer = ProgrammingLanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        language = serializer.save()
        return Response(ProgrammingLanguageSerializer(language).data, status=status.HTTP_201_CREATED)


class AdminLanguageDetailView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get_object(self, pk):
        return ProgrammingLanguage.objects.get(pk=pk)

    def patch(self, request, pk):
        language = self.get_object(pk)
        serializer = ProgrammingLanguageSerializer(language, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        language = serializer.save()
        return Response(ProgrammingLanguageSerializer(language).data)

    def delete(self, request, pk):
        language = self.get_object(pk)
        language.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCourseAssignmentListCreateView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        assignments = CourseAssignment.objects.select_related('course', 'user', 'group', 'assigned_by')
        return Response(CourseAssignmentSerializer(assignments, many=True).data)

    def post(self, request):
        serializer = CourseAssignmentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()
        return Response(CourseAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class AdminCourseAssignmentDetailView(APIView):
    permission_classes = [IsPlatformAdmin]

    def delete(self, request, pk):
        assignment = CourseAssignment.objects.get(pk=pk)
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
