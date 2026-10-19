from rest_framework import serializers

from .models import Lesson
from .progress import get_lesson_unlock_map


class LessonListSerializer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    is_in_review = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'number', 'title', 'slug', 'goal',
            'max_xp', 'status', 'sort_order', 'is_locked', 'is_completed', 'is_in_review',
        ]

    def _unlock_map(self, obj):
        cache = self.context.get('_unlock_map')
        if cache is None:
            request = self.context.get('request')
            course = self.context.get('course')
            if request and course:
                cache = get_lesson_unlock_map(request.user, course)
                self.context['_unlock_map'] = cache
            else:
                cache = {}
        return cache

    def get_is_locked(self, obj):
        return self._unlock_map(obj).get(obj.id, {}).get('is_locked', False)

    def get_is_completed(self, obj):
        return self._unlock_map(obj).get(obj.id, {}).get('is_completed', False)

    def get_is_in_review(self, obj):
        return self._unlock_map(obj).get(obj.id, {}).get('is_in_review', False)


class LessonDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'language', 'number', 'title', 'slug', 'goal',
            'theory_text', 'simple_explanation', 'practice_text',
            'mini_project_text', 'summary_text', 'max_xp', 'badge',
            'version', 'status', 'content_format', 'assets_json', 'sort_order',
            'created_at', 'updated_at',
        ]


class LessonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'language', 'number', 'title', 'slug', 'goal',
            'theory_text', 'simple_explanation', 'practice_text',
            'mini_project_text', 'summary_text', 'max_xp', 'badge',
            'version', 'status', 'content_format', 'source_import_id',
            'assets_json', 'sort_order',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data.setdefault('author', request.user)
        return super().create(validated_data)
