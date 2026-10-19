from django.contrib.auth import get_user_model
from rest_framework import serializers

from .avatar import user_avatar_url
from .models import Group, GroupUser

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'role',
            'avatar', 'is_active', 'last_login', 'date_joined', 'children',
        ]
        read_only_fields = ['id', 'last_login', 'date_joined', 'children']

    def get_avatar(self, obj):
        return user_avatar_url(obj, self.context.get('request'))

    def get_children(self, obj):
        if obj.role != User.Role.PARENT:
            return []
        from .parent_serializers import ChildUserSerializer
        return ChildUserSerializer(obj.children.all(), many=True).data


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'display_name',
            'role', 'avatar', 'is_active',
        ]
        extra_kwargs = {
            'email': {'validators': []},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким логином уже существует.')
        return value

    def validate(self, attrs):
        role = attrs.get('role', User.Role.STUDENT)
        username = attrs.get('username', '')
        email = attrs.get('email', '').strip()

        if role == User.Role.STUDENT:
            if not email:
                email = f'{username}@localhost'
            base_email = email
            suffix = 1
            while User.objects.filter(email__iexact=email).exists():
                email = f'{username}.{suffix}@localhost'
                suffix += 1
            attrs['email'] = email
        elif email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'Пользователь с таким email уже существует.'})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)
    child_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'display_name',
            'role', 'avatar', 'is_active', 'child_ids',
        ]

    def update(self, instance, validated_data):
        child_ids = validated_data.pop('child_ids', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if child_ids is not None and instance.role == User.Role.PARENT:
            students = User.objects.filter(pk__in=child_ids, role=User.Role.STUDENT)
            instance.children.set(students)
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class GroupUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = GroupUser
        fields = ['id', 'user', 'user_id', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class GroupSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__in=[User.Role.TEACHER, User.Role.ADMIN, User.Role.SUPERADMIN]),
        source='teacher',
        write_only=True,
        required=False,
        allow_null=True,
    )
    members = serializers.SerializerMethodField()
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Group
        fields = [
            'id', 'title', 'description', 'teacher', 'teacher_id',
            'is_active', 'members', 'member_ids', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_members(self, obj):
        users = User.objects.filter(group_memberships__group=obj)
        return UserSerializer(users, many=True).data

    def _sync_members(self, group, member_ids):
        if member_ids is None:
            return
        current_ids = set(
            GroupUser.objects.filter(group=group).values_list('user_id', flat=True)
        )
        target_ids = set(member_ids)
        for uid in target_ids - current_ids:
            GroupUser.objects.get_or_create(group=group, user_id=uid)
        GroupUser.objects.filter(group=group, user_id__in=current_ids - target_ids).delete()

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', None)
        group = super().create(validated_data)
        self._sync_members(group, member_ids)
        return group

    def update(self, instance, validated_data):
        member_ids = validated_data.pop('member_ids', None)
        group = super().update(instance, validated_data)
        self._sync_members(group, member_ids)
        return group
