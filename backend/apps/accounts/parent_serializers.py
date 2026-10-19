from rest_framework import serializers

from .models import User


class ChildUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name',
            'is_active', 'last_login', 'date_joined',
        ]
        read_only_fields = fields


class ParentChildCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким логином уже существует.')
        return value

    def create(self, validated_data):
        parent = self.context['parent']
        email = validated_data.get('email') or f"{validated_data['username']}@parent.local"
        if User.objects.filter(email__iexact=email).exists():
            email = f"{validated_data['username']}.{parent.id}@parent.local"
        child = User(
            username=validated_data['username'],
            email=email,
            display_name=validated_data.get('display_name') or validated_data['username'],
            role=User.Role.STUDENT,
        )
        child.set_password(validated_data['password'])
        child.save()
        parent.children.add(child)
        return child


class ParentChildPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)
