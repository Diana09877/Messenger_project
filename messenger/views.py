from rest_framework import generics
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Chat, Message
from drf_spectacular.utils import extend_schema
from .serializers import (
    ChatCreateSerializer,
    ChatListSerializer,
    MessageCreateSerializer,
    ChatDetailSerializer,
    ChatUpdateSerializer
)


class MessageCreateAPIView(CreateAPIView):
    """Создание сообщения и добавление его в чат"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=MessageCreateSerializer,
        responses={201: MessageCreateSerializer, 400: None}
    )

    def post(self, request):
        serializer = MessageCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            message = serializer.save()
            return Response(MessageCreateSerializer(message).data, status=201)
        return Response(serializer.errors, status=400)


class MessageLikeAPIView(APIView):
    """Поставить или снять лайк с сообщения"""
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id)
        if user not in message.chat.participants.all():
            return Response(status=403)
        liked = message.likes.filter(id=user.id).exists()
        if liked:
            message.likes.remove(user)
        else:
            message.likes.add(user)

        return Response({'liked': not liked}, status=200)


class ChatListAPIView(generics.ListAPIView):
    """Список чатов пользователя с последним сообщением"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatListSerializer

    def get_queryset(self):
        return (
            Chat.objects
            .filter(participants=self.request.user)
            .order_by('-created_at')
        )

class ChatDetailAPIView(generics.RetrieveAPIView):
    """Получение информации о чате"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatDetailSerializer
    lookup_url_kwarg = 'chat_id'

    def get_queryset(self):
        return Chat.objects.all()

    def retrieve(self, request, *args, **kwargs):
        chat = self.get_object()

        if request.user not in chat.participants.all():
            if chat.is_group:
                phones = [p.phone_number for p in chat.participants.all()]
                return Response({
                    'chat_id': chat.id,
                    'chat_name': chat.chat_name,
                    'is_group': chat.is_group,
                    'participants': phones,
                    'messages': [],
                    'access': False,
                })
            # Если это личный чат и пользователь не участник — запрещаем доступ
            return Response({'detail': 'Forbidden'}, status=403)

        data = self.get_serializer(chat).data
        data['access'] = True
        return Response(data, status=200)


class ChatCreateAPIView(APIView):
    """Создание нового чата"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            chat = serializer.save()
            return Response(ChatCreateSerializer(chat).data, status=201)
        return Response(serializer.errors, status=400)


class ChatUpdateAPIView(APIView):
    """Обновить название группового чата"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        chat = get_object_or_404(Chat, pk=pk)

        if request.user not in chat.participants.all():
            return Response({'error': 'Вы не участник этого чата.'}, status=403)

        # Проверка: только для групп
        if not chat.is_group:
            return Response({'error': 'Название можно менять только у групповых чатов.'}, status=400)

        serializer = ChatUpdateSerializer(chat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)


class ChatJoinAPIView(APIView):
    """Вступить в чат по ID (только для групп)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)

        if not chat.is_group:
            return Response({'error': 'Это не групповой чат.'}, status=400)

        if request.user in chat.participants.all():
            return Response({'message': 'Вы уже участник чата.'}, status=200)

        chat.participants.add(request.user)
        return Response({'message': 'Вы вступили в группу.'}, status=200)


class ChatSearchAPIView(generics.ListAPIView):
    """Поиск чата"""
    serializer_class = ChatListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('q', '')

        return Chat.objects.filter(
            participants=user,
            chat_name__icontains=query
        )