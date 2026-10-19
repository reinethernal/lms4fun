from rest_framework import serializers

from .models import ImportJob


class ImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportJob
        fields = [
            'id', 'import_type', 'file_name', 'status',
            'result_json', 'errors_json', 'created_at', 'finished_at',
        ]
        read_only_fields = fields


class ImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    data = serializers.JSONField(required=False)
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if not attrs.get('file') and not attrs.get('data'):
            raise serializers.ValidationError('Укажите file или data.')
        return attrs
