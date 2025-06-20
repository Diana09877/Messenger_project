from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import CustomUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileUpdateSerializer,
    UserSerializer
)


@extend_schema(
    summary="Получить или обновить профиль",
    description="Позволяет получить, обновить PUT или частично обновить PATCH профиль текущего пользователя",
    responses={200: UserSerializer}
)
class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """Просмотр и редактирование профиля пользователя"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        # Если GET  вернуть полный профиль, иначе для обновления
        if self.request.method == 'GET':
            return UserSerializer
        return UserProfileUpdateSerializer


@extend_schema(
    summary="Регистрация нового пользователя",
    description="Создание пользователя и получение токена доступа",
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(description="Успешная регистрация с токеном"),
        400: OpenApiResponse(description="Ошибки валидации")
    }
)
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


@extend_schema(
    summary="Вход пользователя",
    description="Авторизация по номеру телефона и паролю. Возвращает токен",
    request=UserLoginSerializer,
    responses={
        200: OpenApiResponse(description="Успешный вход и получение токена"),
        400: OpenApiResponse(description="Неверные данные или ошибки валидации")
    }
)
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


@extend_schema(
    summary="Поиск пользователей",
    description="Поиск пользователей по номеру телефона или имени. Исключает текущего пользователя",
    parameters=[
        OpenApiParameter(
            name='search',
            description='Поисковый запрос (номер телефона или имя)',
            required=False,
            type=str,
            location=OpenApiParameter.QUERY
        )
    ],
    responses={200: UserSerializer(many=True)}
)
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

