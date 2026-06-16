from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from access_control.permissions import AuthStatusMixin
from users.authentication import generate_token
from users.models import AuthToken, CustomUser
from users.serializers import LoginSerializer, ProfileSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'message': 'Регистрация успешна', 'user_id': user.id},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        AuthToken.objects.filter(user=user).delete()
        token = AuthToken.objects.create(user=user, key=generate_token())

        return Response({
            'token': token.key,
            'user': ProfileSerializer(user).data,
        })


class LogoutView(AuthStatusMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        AuthToken.objects.filter(user=request.user).delete()
        return Response(
            {'message': 'Выход выполнен'},
            status=status.HTTP_200_OK,
        )


class ProfileView(AuthStatusMixin, generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class DeleteAccountView(AuthStatusMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request):
        user = request.user
        AuthToken.objects.filter(user=user).delete()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response(
            {'message': 'Аккаунт деактивирован'},
            status=status.HTTP_200_OK,
        )
