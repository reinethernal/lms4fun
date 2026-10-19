from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Group, User
from .parent_serializers import ChildUserSerializer
from .permissions import IsStaffMember


class StaffParentSerializer(serializers.ModelSerializer):
    children = ChildUserSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name',
            'is_active', 'last_login', 'children',
        ]


class StaffParentChildrenSerializer(serializers.Serializer):
    child_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


def _staff_accessible_student_ids(user) -> set[int] | None:
    if user.is_platform_admin or user.is_superadmin:
        return None
    if user.is_teacher:
        return set(
            Group.objects.filter(teacher=user).values_list(
                'memberships__user_id',
                flat=True,
            )
        )
    return set()


class StaffParentsListView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        parents = User.objects.filter(role=User.Role.PARENT).prefetch_related('children').order_by('username')
        return Response(StaffParentSerializer(parents, many=True).data)


class StaffStudentsListView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        students = User.objects.filter(role=User.Role.STUDENT).order_by('username')
        allowed = _staff_accessible_student_ids(request.user)
        if allowed is not None:
            students = students.filter(pk__in=allowed)
        return Response(ChildUserSerializer(students, many=True).data)


class StaffParentChildrenView(APIView):
    permission_classes = [IsStaffMember]

    def patch(self, request, pk):
        try:
            parent = User.objects.get(pk=pk, role=User.Role.PARENT)
        except User.DoesNotExist:
            return Response({'detail': 'Родитель не найден.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StaffParentChildrenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        child_ids = serializer.validated_data['child_ids']

        students = User.objects.filter(pk__in=child_ids, role=User.Role.STUDENT)
        if students.count() != len(set(child_ids)):
            return Response({'detail': 'Можно привязывать только учеников.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed = _staff_accessible_student_ids(request.user)
        if allowed is not None and not set(child_ids).issubset(allowed):
            return Response(
                {'detail': 'Можно привязывать только учеников из ваших групп.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        parent.children.set(students)
        parent = User.objects.prefetch_related('children').get(pk=parent.pk)
        return Response(StaffParentSerializer(parent).data)
