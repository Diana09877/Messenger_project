from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Chat, Message
from .serializers import (
    ChatCreateSerializer, ChatListSerializer, MessageCreateSerializer,
    ChatDetailSerializer, ChatUpdateSerializer
)

class MessageCreateAPIView(APIView):
    """Создание сообщения и добавление его в чат"""
    permission_classes = [IsAuthenticated]

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

        # Проверяем, есть ли у пользователя доступ к чату
        if user not in message.chat.participants.all():
            return Response(status=403)

        # Переключаем лайк
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


class ChatDetailAPIView(APIView):
    """Получение информации о чате (только если пользователь участник)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)

        if request.user not in chat.participants.all():
            if chat.is_group:
                participants = chat.participants.all()
                participant_phones = [participant.phone_number for participant in participants]

                return Response({
                    'chat_id': chat.id,
                    'chat_name': chat.chat_name,
                    'is_group': chat.is_group,
                    'participants': participant_phones,
                    'messages': []  # сообщения не показываем, так как не участник
                }, status=200)
            else:
                # Если это личный чат и пользователь не участник — запрещаем доступ
                return Response({'detail': 'Доступ запрещён'}, status=403)

        # Если пользователь участник чата — сериализуем и отдаём полную информацию
        serializer = ChatDetailSerializer(chat, context={'request': request})
        return Response(serializer.data, status=200)


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
