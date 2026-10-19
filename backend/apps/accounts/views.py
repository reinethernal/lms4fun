from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsPlatformAdmin
from .serializers import (
    GroupSerializer,
    LoginSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .models import Group, User
from .services import delete_user_account, reset_student_statistics

from apps.gamification.models import UserBadge
from apps.gamification.serializers import UserBadgeSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None or not user.is_active:
            return Response({'detail': 'Неверные учётные данные.'}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        from apps.notifications.services import log_audit

        log_audit(user, 'auth.login', 'user', user.id, {}, request)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'Вы вышли из системы.'})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class AdminUserListCreateView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        users = User.objects.all().order_by('username')
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get_object(self, pk):
        return User.objects.get(pk=pk)

    def get(self, request, pk):
        user = self.get_object(pk)
        return Response(UserSerializer(user).data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)

    def delete(self, request, pk):
        user = self.get_object(pk)
        if user == request.user:
            return Response({'detail': 'Нельзя удалить свой аккаунт.'}, status=status.HTTP_400_BAD_REQUEST)
        from apps.notifications.services import log_audit

        user_id = user.id
        username = user.username
        delete_user_account(user)
        log_audit(request.user, 'user.delete', 'user', user_id, {'username': username}, request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserResetStatisticsView(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        include_submissions = bool(request.data.get('include_submissions', False))
        try:
            result = reset_student_statistics(user, include_submissions=include_submissions)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from apps.notifications.services import log_audit

        log_audit(
            request.user,
            'user.reset_statistics',
            'user',
            user.id,
            {'username': user.username, **result},
            request,
        )
        return Response({
            'detail': 'Статистика ученика сброшена.',
            **result,
        })


class AdminUserBadgesView(APIView):
    permission_classes = [IsPlatformAdmin]

    def _get_student(self, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
        if user.role != User.Role.STUDENT:
            return False
        return user

    def get(self, request, pk):
        user = self._get_student(pk)
        if user is None:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)
        if user is False:
            return Response({'detail': 'Бейджи доступны только для учеников.'}, status=status.HTTP_400_BAD_REQUEST)
        badges = UserBadge.objects.filter(user=user).select_related('badge', 'awarded_by')
        return Response(UserBadgeSerializer(badges, many=True, context={'request': request}).data)

    def post(self, request, pk):
        from apps.gamification.models import Badge
        from apps.gamification.services import award_badge_to_user
        from apps.notifications.services import log_audit

        user = self._get_student(pk)
        if user is None:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)
        if user is False:
            return Response({'detail': 'Бейджи доступны только для учеников.'}, status=status.HTTP_400_BAD_REQUEST)

        badge_id = request.data.get('badge_id')
        if not badge_id:
            return Response({'detail': 'Укажите badge_id.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            badge = Badge.objects.get(pk=badge_id, is_active=True)
        except Badge.DoesNotExist:
            return Response({'detail': 'Бейдж не найден или неактивен.'}, status=status.HTTP_404_NOT_FOUND)

        if UserBadge.objects.filter(user=user, badge=badge).exists():
            return Response({'detail': 'Бейдж уже выдан.'}, status=status.HTTP_409_CONFLICT)

        user_badge = award_badge_to_user(user, badge, request.user)
        log_audit(
            request.user,
            'badge.award',
            'user_badge',
            user_badge.id,
            {'user_id': user.id, 'badge_id': badge.id, 'badge_title': badge.title},
            request,
        )
        return Response(
            UserBadgeSerializer(user_badge, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdminUserBadgeRevokeView(APIView):
    permission_classes = [IsPlatformAdmin]

    def delete(self, request, pk, badge_id):
        from apps.gamification.services import revoke_badge_from_user
        from apps.notifications.services import log_audit

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)
        if user.role != User.Role.STUDENT:
            return Response({'detail': 'Бейджи доступны только для учеников.'}, status=status.HTTP_400_BAD_REQUEST)

        user_badge = UserBadge.objects.filter(user=user, badge_id=badge_id).select_related('badge').first()
        if not user_badge:
            return Response({'detail': 'Бейдж не найден у ученика.'}, status=status.HTTP_404_NOT_FOUND)

        badge_title = user_badge.badge.title
        try:
            revoke_badge_from_user(user, badge_id)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)

        log_audit(
            request.user,
            'badge.revoke',
            'user_badge',
            user_badge.id,
            {'user_id': user.id, 'badge_id': badge_id, 'badge_title': badge_title},
            request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminGroupListCreateView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        groups = Group.objects.select_related('teacher').all()
        return Response(GroupSerializer(groups, many=True).data)

    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)


class AdminGroupDetailView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get_object(self, pk):
        return Group.objects.select_related('teacher').get(pk=pk)

    def patch(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupSerializer(group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(GroupSerializer(group).data)

    def delete(self, request, pk):
        group = self.get_object(pk)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
