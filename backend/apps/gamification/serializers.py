from rest_framework import serializers

from apps.courses.models import Course, ProgrammingLanguage

from .models import Badge, UserBadge, UserProgress, XPTransaction


class UserProgressSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = UserProgress
        fields = [
            'id', 'course', 'course_title', 'lesson', 'task',
            'xp_earned', 'tasks_completed', 'lessons_completed',
            'last_activity_at', 'progress_json',
        ]


class BadgeAwardSerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ['id', 'title', 'description', 'icon_url', 'level']

    def get_icon_url(self, obj):
        if obj.icon_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon_image.url)
            return obj.icon_image.url
        return obj.icon or ''


class BadgeSerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = [
            'id', 'title', 'description', 'icon', 'icon_url', 'badge_type', 'level',
            'condition_type', 'condition_key', 'condition_value', 'condition_params',
            'language', 'course', 'is_active',
        ]

    def get_icon_url(self, obj):
        if obj.icon_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.icon_image.url)
            return obj.icon_image.url
        return obj.icon or ''


class BadgeWriteSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        allow_null=True,
        required=False,
    )
    language = serializers.PrimaryKeyRelatedField(
        queryset=ProgrammingLanguage.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Badge
        fields = [
            'title', 'description', 'icon', 'icon_image', 'badge_type', 'level',
            'condition_type', 'condition_key', 'condition_value', 'condition_params',
            'language', 'course', 'is_active',
        ]

    def validate_condition_value(self, value):
        if value in ('', None):
            return None
        return value

    def validate_condition_params(self, value):
        if value in ('', None):
            return {}
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError('Некорректный JSON в condition_params')
        return value


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    awarded_by = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'awarded_at', 'awarded_by', 'source']

    def get_awarded_by(self, obj):
        if not obj.awarded_by_id:
            return None
        user = obj.awarded_by
        return {
            'id': user.id,
            'username': user.username,
            'display_name': user.display_name or user.username,
        }

    def get_source(self, obj) -> str:
        return 'manual' if obj.awarded_by_id else 'auto'


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    avatar = serializers.CharField(allow_blank=True)
    total_xp = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()
