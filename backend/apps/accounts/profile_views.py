from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .profile import build_self_profile, build_student_profile, can_view_student_profile
from .profile_serializers import ProfileUpdateSerializer, StudentProfileSerializer


class ProfileMeView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        data = build_self_profile(request.user, request=request)
        return Response(StudentProfileSerializer(data).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        data = build_self_profile(request.user, request=request)
        return Response(StudentProfileSerializer(data).data)


class StudentProfileView(APIView):
    def get(self, request, pk):
        try:
            student = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if student.role != User.Role.STUDENT:
            return Response({'detail': 'Профиль доступен только для учеников.'}, status=status.HTTP_400_BAD_REQUEST)

        if not can_view_student_profile(request.user, student):
            return Response({'detail': 'Нет доступа.'}, status=status.HTTP_403_FORBIDDEN)

        data = build_student_profile(student, request.user, request=request)
        return Response(StudentProfileSerializer(data).data)
