from rest_framework import serializers

from .models import Task, TestCase


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ['id', 'stdin', 'expected_stdout', 'expected_stderr', 'is_hidden', 'sort_order']


def _task_has_input(starter_code: str) -> bool:
    import re
    return bool(re.search(r'\binput\s*\(', starter_code or ''))


class TaskListSerializer(serializers.ModelSerializer):
    requires_stdin = serializers.SerializerMethodField()
    stdin_hint = serializers.SerializerMethodField()
    visible_tests_preview = serializers.SerializerMethodField()
    input_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'lesson', 'language', 'title', 'description', 'task_type',
            'starter_code', 'max_xp', 'difficulty', 'is_required', 'sort_order',
            'requires_stdin', 'stdin_hint', 'visible_tests_preview', 'input_count',
        ]

    def get_requires_stdin(self, obj: Task) -> bool:
        if obj.checker_type == Task.CheckerType.STDIN_STDOUT:
            return True
        return _task_has_input(obj.starter_code)

    def get_stdin_hint(self, obj: Task) -> str:
        tests = obj.visible_tests_json or []
        if tests and isinstance(tests[0], dict):
            return str(tests[0].get('stdin', ''))
        return ''

    def get_visible_tests_preview(self, obj: Task) -> list:
        preview = []
        for test in obj.visible_tests_json or []:
            if isinstance(test, dict):
                preview.append({
                    'stdin': test.get('stdin', ''),
                    'expected_stdout': test.get('expected_stdout', ''),
                })
        return preview

    def get_input_count(self, obj: Task) -> int:
        import re
        return len(re.findall(r'\binput\s*\(', obj.starter_code or ''))


class TaskDetailSerializer(serializers.ModelSerializer):
    test_cases = TestCaseSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'lesson', 'language', 'title', 'description', 'task_type',
            'starter_code', 'visible_tests_json', 'max_xp', 'difficulty',
            'is_required', 'sort_order', 'test_cases',
        ]


class TaskWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'lesson', 'language', 'slug', 'title', 'description', 'task_type',
            'starter_code', 'solution_template', 'stdin', 'expected_stdout',
            'expected_stderr', 'checker_type', 'checker_code',
            'visible_tests_json', 'hidden_tests_json', 'checker_config_json',
            'max_xp', 'difficulty', 'is_required', 'sort_order',
        ]
        read_only_fields = ['id']
