from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsPlatformAdmin

from .models import Badge, UserBadge, UserProgress
from .serializers import (
    BadgeSerializer,
    BadgeWriteSerializer,
    LeaderboardEntrySerializer,
    UserBadgeSerializer,
    UserProgressSerializer,
)
from .services import get_leaderboard


class MyProgressView(APIView):
    def get(self, request):
        progress = UserProgress.objects.filter(user=request.user).select_related('course', 'lesson', 'task')
        return Response(UserProgressSerializer(progress, many=True).data)


class LeaderboardView(APIView):
    def get(self, request):
        course_id = request.query_params.get('course_id')
        group_id = request.query_params.get('group_id')
        entries = get_leaderboard(
            course_id=int(course_id) if course_id else None,
            group_id=int(group_id) if group_id else None,
            request=request,
        )
        return Response(LeaderboardEntrySerializer(entries, many=True).data)


class MyBadgesView(APIView):
    def get(self, request):
        badges = UserBadge.objects.filter(user=request.user).select_related('badge')
        serializer = UserBadgeSerializer(badges, many=True, context={'request': request})
        return Response(serializer.data)


class AdminBadgeListCreateView(APIView):
    permission_classes = [IsPlatformAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        badges = Badge.objects.select_related('language', 'course').all()
        serializer = BadgeSerializer(badges, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = BadgeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        badge = serializer.save()
        return Response(
            BadgeSerializer(badge, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdminBadgeDetailView(APIView):
    permission_classes = [IsPlatformAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        return Badge.objects.select_related('language', 'course').get(pk=pk)

    def patch(self, request, pk):
        badge = self.get_object(pk)
        serializer = BadgeWriteSerializer(badge, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        badge = serializer.save()
        return Response(BadgeSerializer(badge, context={'request': request}).data)

    def delete(self, request, pk):
        badge = self.get_object(pk)
        if badge.icon_image:
            badge.icon_image.delete(save=False)
        badge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
