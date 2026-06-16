from django.contrib.auth import authenticate
from rest_framework import serializers

from users.models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_repeat = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'password_repeat')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_repeat']:
            raise serializers.ValidationError({'password_repeat': 'Пароли не совпадают.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_repeat')
        password = validated_data.pop('password')
        validated_data['username'] = validated_data.get('email')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({'email': 'Пользователь с таким email не найден.'})

        if not user.is_active:
            raise serializers.ValidationError({'email': 'Учетная запись деактивирована.'})

        user = authenticate(username=user.username, password=password)
        if user is None:
            raise serializers.ValidationError({'password': 'Неверный пароль.'})

        attrs['user'] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id', 'email', 'role')
