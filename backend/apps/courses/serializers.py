from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.models import Group

from .models import Course, CourseAssignment, ProgrammingLanguage

User = get_user_model()


class ProgrammingLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammingLanguage
        fields = [
            'id', 'name', 'slug', 'judge0_language_id', 'version',
            'default_time_limit', 'default_memory_limit', 'default_output_limit',
            'starter_code', 'editor_mode', 'is_active',
        ]


class CourseListSerializer(serializers.ModelSerializer):
    primary_language = ProgrammingLanguageSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'primary_language',
            'age_from', 'age_to', 'level', 'status', 'cover_image',
            'visibility', 'version',
        ]


class CourseDetailSerializer(CourseListSerializer):
    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + [
            'settings_json', 'created_at', 'updated_at',
        ]


class CourseWriteSerializer(serializers.ModelSerializer):
    primary_language_id = serializers.PrimaryKeyRelatedField(
        queryset=ProgrammingLanguage.objects.all(),
        source='primary_language',
    )

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'primary_language_id',
            'age_from', 'age_to', 'level', 'author', 'version', 'status',
            'cover_image', 'visibility', 'settings_json',
        ]
        read_only_fields = ['id', 'author']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data.setdefault('author', request.user)
        return super().create(validated_data)


class CourseAssignmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), source='course', write_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False,
        allow_null=True,
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source='group',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = CourseAssignment
        fields = [
            'id', 'course', 'course_id', 'user_id', 'group_id',
            'assigned_by', 'available_from', 'deadline', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'assigned_by', 'created_at']

    def validate(self, attrs):
        user = attrs.get('user')
        group = attrs.get('group')
        if not user and not group:
            raise serializers.ValidationError('Укажите user_id или group_id.')
        if user and group:
            raise serializers.ValidationError('Укажите только user_id или group_id.')
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['assigned_by'] = request.user
        return super().create(validated_data)
