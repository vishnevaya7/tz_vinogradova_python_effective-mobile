from django.contrib.auth import login, logout
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from access_control.permissions import AuthStatusMixin
from users.models import CustomUser
from users.serializers import LoginSerializer, ProfileSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(ProfileSerializer(user).data)


class LogoutView(AuthStatusMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(AuthStatusMixin, generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class DeleteAccountView(AuthStatusMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request):
        user = request.user
        logout(request)
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
