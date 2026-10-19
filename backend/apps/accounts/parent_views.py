from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gamification.models import UserBadge, UserProgress
from apps.gamification.serializers import UserBadgeSerializer, UserProgressSerializer
from apps.submissions.models import Submission
from apps.submissions.serializers import AdminSubmissionDetailSerializer, AdminSubmissionListSerializer

from .models import User
from .parent_access import ensure_parent_child
from .parent_serializers import (
    ChildUserSerializer,
    ParentChildCreateSerializer,
    ParentChildPasswordSerializer,
)
from .permissions import IsParent


class ParentChildrenListCreateView(APIView):
    permission_classes = [IsParent]

    def get(self, request):
        children = request.user.children.all().order_by('username')
        return Response(ChildUserSerializer(children, many=True).data)

    def post(self, request):
        serializer = ParentChildCreateSerializer(data=request.data, context={'parent': request.user})
        serializer.is_valid(raise_exception=True)
        child = serializer.save()
        return Response(ChildUserSerializer(child).data, status=status.HTTP_201_CREATED)


class ParentChildPasswordView(APIView):
    permission_classes = [IsParent]

    def patch(self, request, child_id):
        try:
            child = ensure_parent_child(request.user, child_id)
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        serializer = ParentChildPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        child.set_password(serializer.validated_data['password'])
        child.save(update_fields=['password'])
        return Response({'detail': 'Пароль обновлён.'})


class ParentChildProgressView(APIView):
    permission_classes = [IsParent]

    def get(self, request, child_id):
        try:
            child = ensure_parent_child(request.user, child_id)
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        progress = UserProgress.objects.filter(user=child).select_related('course', 'lesson', 'task')
        return Response(UserProgressSerializer(progress, many=True).data)


class ParentChildBadgesView(APIView):
    permission_classes = [IsParent]

    def get(self, request, child_id):
        try:
            child = ensure_parent_child(request.user, child_id)
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        badges = UserBadge.objects.filter(user=child).select_related('badge')
        return Response(
            UserBadgeSerializer(badges, many=True, context={'request': request}).data
        )


class ParentChildSubmissionsListView(APIView):
    permission_classes = [IsParent]

    def get(self, request, child_id):
        try:
            child = ensure_parent_child(request.user, child_id)
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        submissions = (
            Submission.objects.filter(user=child)
            .select_related('user', 'task', 'language')
            .order_by('-submitted_at')[:200]
        )
        return Response(AdminSubmissionListSerializer(submissions, many=True).data)


class ParentChildSubmissionDetailView(APIView):
    permission_classes = [IsParent]

    def get(self, request, child_id, pk):
        try:
            child = ensure_parent_child(request.user, child_id)
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

        submission = (
            Submission.objects.filter(user=child, pk=pk)
            .select_related('user', 'task', 'language')
            .first()
        )
        if submission is None:
            return Response({'detail': 'Решение не найдено.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminSubmissionDetailSerializer(submission).data)
