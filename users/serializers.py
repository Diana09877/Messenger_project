from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import CustomUser


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """ Сериализатор для редактирования профиля пользователя"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'avatar',
            'phone_number',
            'date_of_birth',
        ]
        extra_kwargs = {
            'phone_number': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'avatar': {'required': False},
            'date_of_birth': {'required': False},
        }

    def validate_phone_number(self, value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(id=user.id).filter(phone_number=value).exists():
            raise serializers.ValidationError('Этот номер телефона уже занят')
        return value


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для основных данных пользователя"""
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'phone_number',
            'first_name',
            'last_name',
            'avatar',
            'date_of_birth',
        ]

class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя по номеру и паролю"""
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя с проверкой номера"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            'phone_number',
            'first_name',
            'last_name',
            'password',
        ]

    def validate_phone_number(self, value):
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Такой пользователь уже существует')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)

