from rest_framework import generics, permissions
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Chat, Message
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .serializers import (
    ChatCreateSerializer,
    ChatListSerializer,
    MessageCreateSerializer,
    ChatDetailSerializer,
    ChatUpdateSerializer, MessageDeleteSerializer, ChatDeleteSerializer
)

@extend_schema(
    summary="Создать сообщение",
    description="Создаёт новое сообщение в чате",
    request=MessageCreateSerializer,
    responses={201: MessageCreateSerializer}
)
class MessageCreateAPIView(CreateAPIView):
    """Создание сообщения и добавление его в чат"""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageCreateSerializer


@extend_schema(
    summary="Лайк поставлен или убран",
    description="Добавляет или убирает лайк к сообщению. Только участники чата",
    responses={200: OpenApiResponse(description="Лайк поставлен/убран")},
    parameters=[OpenApiParameter(name='message_id', location=OpenApiParameter.PATH, required=True, type=int)]
)
class MessageLikeAPIView(APIView):
    """Поставить или снять лайк с сообщения"""
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id)
        if user not in message.chat.participants.all():
            return Response(status=403)
        if message.likes.filter(id=user.id).exists():
            message.likes.remove(user)
            liked = False
        else:
            message.likes.add(user)
            liked = True
        return Response({'liked': liked}, status=200)


@extend_schema(
    summary="Список чатов и создание",
    description="Показывает чаты пользователя или создаёт новый чат",
    responses={200: ChatListSerializer, 201: ChatCreateSerializer}
)
class ChatListCreateAPIView(generics.ListCreateAPIView):
    """Показать список чатов или создать новый чат"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatCreateSerializer
        return ChatListSerializer


@extend_schema(
    summary="Получить или обновить чат",
    description="Получает детали чата или обновляет его",
    responses={
        200: ChatDetailSerializer,
        403: OpenApiResponse(description="Нет доступа")
    },
    parameters=[OpenApiParameter(name='pk', location=OpenApiParameter.PATH, required=True, type=int)]
)
class ChatRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """Получить или обновить чат"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Если обновляем  используем один сериализатор,
        # если просто получаем другой
        if self.request.method in ['PATCH', 'PUT']:
            return ChatUpdateSerializer
        return ChatDetailSerializer

    def get_object(self):
        return get_object_or_404(Chat, id=self.kwargs['pk'])

    def retrieve(self, request, *args, **kwargs):
        chat = self.get_object()
        if request.user not in chat.participants.all():
            if chat.is_group:
                return Response({
                    'chat_id': chat.id,
                    'chat_name': chat.chat_name,
                    'is_group': chat.is_group,
                    'participants': [p.phone_number for p in chat.participants.all()],
                    'messages': [],
                })
            return Response({'detail': 'Forbidden'}, status=403)
        data = self.get_serializer(chat).data
        return Response(data, status=200)


@extend_schema(
    summary="Поиск чатов",
    description="Ищет чаты по названию, где участвует пользователь",
    parameters=[OpenApiParameter(name='q', location='query', required=False, type=str)],
    responses={200: ChatListSerializer(many=True)}
)
class ChatSearchAPIView(generics.ListAPIView):
    """Поиск чатов по названию"""
    serializer_class = ChatListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('q', '')

        return Chat.objects.filter(
            participants=user,
            chat_name__icontains=query # Поиск без учёта регистра
        )

@extend_schema(
    summary="Удалить чат",
    request=MessageDeleteSerializer,
    responses={200: OpenApiResponse(description="Чат удален")}
)
class ChatDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)
        if chat.creator != request.user:
            return Response({"error": "Только создатель может удалить этот чат."},
                            status=403)

        if chat.is_group:
            chat.delete()
            return Response({"detail": "Групповой чат удалён."}, status=204)
        else:
            if request.user in chat.participants.all():
                chat.participants.remove(request.user)
                return Response(status=204)
            else:
                return Response({"error": "Вы не участник этого чата."}, status=400)


@extend_schema(
    summary="Удалить сообщение",
    request=MessageDeleteSerializer,
    responses={200: OpenApiResponse(description="Сообщение удалено")}
)
class MessageDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)

        # Только автор сообщения или создатель чата может удалить сообщение
        if message.author != request.user and message.chat.creator != request.user:
            return Response({"error": "Нет прав на удаление этого сообщения."},
                            status=403)

        message.delete()
        return Response({"detail": "Сообщение удалено."}, status=204)