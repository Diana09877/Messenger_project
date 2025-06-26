from rest_framework import generics, permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Chat, Message, MessageLike
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .serializers import (
    ChatCreateSerializer,
    ChatListSerializer,
    MessageCreateSerializer,
    ChatDetailSerializer,
    ChatUpdateSerializer,
    MessageDeleteSerializer,
    ChatDeleteSerializer
)


# permission класс для проверки прав на удаление сообщения
class IsAuthorOrChatCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj — сообщение
        return obj.author == request.user or obj.chat.creator == request.user


@extend_schema(
    summary="Создать сообщение",
    description="Создаёт новое сообщение в чате",
    request=MessageCreateSerializer,
    responses={201: MessageCreateSerializer}
)
class MessageCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageCreateSerializer


@extend_schema(
    summary="Лайк поставлен или убран",
    description="Добавляет или убирает лайк к сообщению. Только участники чата",
    responses={200: OpenApiResponse(description="Лайк поставлен/убран")},
    parameters=[OpenApiParameter(name='message_id', location=OpenApiParameter.PATH, required=True, type=int)]
)
class MessageLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id)

        if user not in message.chat.participants.all():
            return Response(status=403)

        like = MessageLike.objects.filter(user=user, message=message).first()

        if like:
            like.delete()
            liked = False
        else:
            MessageLike.objects.create(user=user, message=message)
            liked = True

        return Response({'liked': liked}, status=200)


@extend_schema(
    summary="Список чатов и создание",
    description="Показывает чаты пользователя или создаёт новый чат",
    responses={200: ChatListSerializer, 201: ChatCreateSerializer}
)
class ChatListCreateAPIView(generics.ListCreateAPIView):
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
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
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
                }, status=status.HTTP_200_OK)
            return Response({'detail': 'Доступ запрещён'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(chat, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Поиск чатов",
    description="Ищет чаты по названию, где участвует пользователь",
    parameters=[OpenApiParameter(name='q', location='query', required=False, type=str)],
    responses={200: ChatListSerializer(many=True)}
)
class ChatSearchAPIView(generics.ListAPIView):
    serializer_class = ChatListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('q', '')
        return Chat.objects.filter(participants=user, chat_name__icontains=query)


@extend_schema(
    summary="Удалить чат",
    request=ChatDeleteSerializer,
    responses={204: OpenApiResponse(description="Чат удалён")}
)
class ChatDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)
        if chat.creator != request.user:
            return Response({"error": "Только создатель может удалить этот чат."}, status=status.HTTP_403_FORBIDDEN)
        if chat.is_group:
            chat.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            if request.user in chat.participants.all():
                chat.participants.remove(request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "Вы не участник этого чата."}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Удалить сообщение",
    request=MessageDeleteSerializer,
    responses={204: OpenApiResponse(description="Сообщение удалено")}
)
class MessageDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAuthorOrChatCreator]

    def delete(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        self.check_object_permissions(request, message)
        message.is_deleted = True
        message.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
