from rest_framework import serializers

from .models import User

MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}


class ProfileUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    avatar = serializers.URLField(required=False, allow_blank=True, max_length=500)
    avatar_image = serializers.ImageField(required=False, allow_null=True)
    remove_avatar = serializers.BooleanField(required=False, default=False)
    password = serializers.CharField(required=False, write_only=True, min_length=6)
    password_confirm = serializers.CharField(required=False, write_only=True, min_length=6)

    def validate_avatar_image(self, value):
        if value is None:
            return value
        if value.size > MAX_AVATAR_SIZE:
            raise serializers.ValidationError('Максимальный размер файла — 2 МБ.')
        content_type = getattr(value, 'content_type', '') or ''
        if content_type and content_type not in ALLOWED_AVATAR_TYPES:
            raise serializers.ValidationError('Допустимые форматы: JPEG, PNG, WebP, GIF.')
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if password or password_confirm:
            if not password or not password_confirm:
                raise serializers.ValidationError('Укажите пароль и подтверждение.')
            if password != password_confirm:
                raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})
        if not any(
            k in attrs
            for k in ('display_name', 'avatar', 'avatar_image', 'remove_avatar', 'password')
        ):
            raise serializers.ValidationError('Нет данных для обновления.')
        return attrs

    def update(self, instance: User, validated_data):
        if validated_data.pop('remove_avatar', False):
            if instance.avatar_image:
                instance.avatar_image.delete(save=False)
            instance.avatar_image = None
            instance.avatar = ''

        if 'display_name' in validated_data:
            instance.display_name = validated_data['display_name']
        if 'avatar' in validated_data:
            instance.avatar = validated_data['avatar']
        if 'avatar_image' in validated_data:
            new_image = validated_data['avatar_image']
            if new_image is None:
                if instance.avatar_image:
                    instance.avatar_image.delete(save=False)
                instance.avatar_image = None
            else:
                if instance.avatar_image:
                    instance.avatar_image.delete(save=False)
                instance.avatar_image = new_image
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class StudentProfileSerializer(serializers.Serializer):
    user = serializers.DictField()
    stats = serializers.DictField()
    progress = serializers.ListField()
    badges = serializers.ListField()
    skill_highlights = serializers.DictField()
    recent_submissions = serializers.ListField()
    permissions = serializers.DictField()
