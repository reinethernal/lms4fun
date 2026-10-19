from rest_framework import serializers

from .models import CodeRun, Submission


class CodeRunRequestSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField(required=False, allow_null=True)
    task_id = serializers.IntegerField(required=False, allow_null=True)
    language = serializers.SlugField()
    source_code = serializers.CharField()
    stdin = serializers.CharField(required=False, allow_blank=True, default='')
    repl_mode = serializers.BooleanField(required=False, default=False)


class CodeRunResponseSerializer(serializers.ModelSerializer):
    language = serializers.SlugField(source='language.slug')

    class Meta:
        model = CodeRun
        fields = [
            'status', 'language', 'stdout', 'stderr', 'compile_output',
            'execution_time', 'memory_used',
        ]


class SubmissionCreateSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    source_code = serializers.CharField()


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = [
            'id', 'task', 'language', 'code', 'stdout', 'stderr', 'compile_output',
            'status', 'score', 'xp_awarded', 'checker_result',
            'submitted_at', 'checked_at', 'teacher_comment',
        ]
        read_only_fields = fields


class SubmissionResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    xp_awarded = serializers.IntegerField()
    message = serializers.CharField()
    new_badges = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    failed_test_index = serializers.IntegerField(required=False, allow_null=True)
    expected = serializers.CharField(required=False, allow_blank=True)
    got = serializers.CharField(required=False, allow_blank=True)
    is_hidden = serializers.BooleanField(required=False)


class SubmissionReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['accepted', 'rejected'])
    teacher_comment = serializers.CharField(required=False, allow_blank=True, default='')


class AdminSubmissionReviewerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()


class AdminSubmissionUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()


class AdminSubmissionTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    lesson_title = serializers.CharField(required=False, allow_blank=True)


class AdminSubmissionListSerializer(serializers.ModelSerializer):
    user = AdminSubmissionUserSerializer(read_only=True)
    task = serializers.SerializerMethodField()
    language = serializers.SlugField(source='language.slug', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'user', 'task', 'language', 'status',
            'xp_awarded', 'submitted_at',
        ]

    def get_task(self, obj):
        lesson_title = ''
        if obj.task_id and getattr(obj.task, 'lesson_id', None):
            lesson_title = obj.task.lesson.title
        return {
            'id': obj.task_id,
            'title': obj.task.title,
            'lesson_title': lesson_title,
        }


class AdminSubmissionDetailSerializer(serializers.ModelSerializer):
    user = AdminSubmissionUserSerializer(read_only=True)
    task = serializers.SerializerMethodField()
    language = serializers.SlugField(source='language.slug', read_only=True)
    checked_by = AdminSubmissionReviewerSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'user', 'task', 'language', 'code', 'stdout', 'stderr',
            'compile_output', 'status', 'score', 'xp_awarded', 'checker_result',
            'submitted_at', 'checked_at', 'checked_by', 'teacher_comment',
        ]

    def get_task(self, obj):
        lesson_title = ''
        if obj.task_id and getattr(obj.task, 'lesson_id', None):
            lesson_title = obj.task.lesson.title
        return {
            'id': obj.task_id,
            'title': obj.task.title,
            'lesson_title': lesson_title,
        }
