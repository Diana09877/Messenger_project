from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileUpdateSerializer,
    UserSerializer
)

class UserProfileAPIView(APIView):
    """Просмотр и редактирование профиля пользователя"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=200)

    def put(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class UserRegistrationAPIView(APIView):
    """Регистрация нового пользователя"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Создание пользователя и выдача токена"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'phone_number': user.phone_number,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'token': token.key,
            }, status=201)
        return Response(serializer.errors, status=400)


class UserLoginAPIView(APIView):
    """Вход пользователя"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        phone_number = serializer.validated_data['phone_number']
        password = serializer.validated_data['password']

        try:
            user = CustomUser.objects.get(phone_number=phone_number)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Неверный номер телефона или пароль'}, status=400)

        if not user.check_password(password):
            return Response({'error': 'Неверный номер телефона или пароль'}, status=400)

        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=200)


class UserSearchAPIView(generics.ListAPIView):
    """Поиск пользователей по номеру телефона"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Фильтрация пользователей по запросу"""
        user = self.request.user
        search_query = self.request.query_params.get('search', '').strip()

        if not search_query:
            return CustomUser.objects.none()

        queryset = CustomUser.objects.filter(
            Q(phone_number__icontains=search_query) |
            Q(first_name__icontains=search_query)
        ).exclude(id=user.id)

        return queryset

