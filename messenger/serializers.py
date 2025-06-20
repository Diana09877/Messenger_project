from users.models import CustomUser
from rest_framework import serializers
from .models import Message, Chat
from users.serializers import UserSerializer
from django.utils.timesince import timesince


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения сообщений"""
    author = UserSerializer(read_only=True)
    chat_id = serializers.IntegerField(read_only=True)
    liked = serializers.SerializerMethodField()
    liked_by = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'chat_id',
            'author',
            'content',
            'created_at',
            'liked',
            'liked_by'
        ]

    def get_liked(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return False
        return obj.likes.filter(id=request.user.id).exists()

    def get_liked_by(self, obj):
        return [
            user.first_name or user.phone_number
            for user in obj.likes.all()
        ]


class MessageCreateSerializer(serializers.ModelSerializer):
    """Сериализует данные для создания новых сообщений"""
    chat_id = serializers.IntegerField(write_only=True)
    content = serializers.CharField()

    class Meta:
        model = Message
        fields = [
            'id',
            'content',
            'chat_id',
        ]

    def validate_chat_id(self, value):
        if not Chat.objects.filter(id=value).exists():
            raise serializers.ValidationError('Чат с таким ID не найден')
        return value

    def create(self, validated_data):
        chat_id = validated_data.pop('chat_id')
        chat = Chat.objects.get(id=chat_id)
        author = self.context['request'].user
        return Message.objects.create(
            chat=chat,
            author=author,
            content=validated_data['content']
        )


class ChatListSerializer(serializers.ModelSerializer):
    """Список чатов с краткой информацией"""
    chat_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_time = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'chat_name',
            'avatar',
            'last_message',
            'last_time',

        ]

    def get_other_user(self, obj):
        user = self.context['request'].user
        participants = obj.participants.exclude(id=user.id)
        if obj.chat_name:
            return None
        return participants.first()

    def get_chat_name(self, obj):
        if obj.chat_name:
            return obj.chat_name
        other_user = self.get_other_user(obj)
        if other_user:
            return other_user.phone_number
        return 'Без имени'

    def get_avatar(self, obj):
        other_user = self.get_other_user(obj)
        if other_user and other_user.avatar:
            return other_user.avatar.url
        return None

    def get_last_message(self, obj):
        last_message = Message.objects.filter(chat=obj).order_by('-created_at').first()
        if last_message:
            return last_message.content
        return ''

    def get_last_time(self, obj):
        last_message = Message.objects.filter(chat=obj).order_by('-created_at').first()
        if last_message:
            return timesince(last_message.created_at)
        return None


class ChatDetailSerializer(serializers.ModelSerializer):
    """Полная информация о чате"""
    chat_name = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'chat_name',
            'messages',
            'is_group',
            'participants',
        ]

    def get_chat_name(self, chat):
        if chat.chat_name:
            return chat.chat_name
        user = self.context['request'].user
        other = chat.participants.exclude(id=user.id).first()
        return other.phone_number if other else "Неизвестный"

    def get_messages(self, chat):
        messages = chat.messages.order_by('created_at')
        return MessageSerializer(messages, many=True, context=self.context).data

    def get_participants(self, chat):
        return [user.phone_number for user in chat.participants.all()]


class ChatCreateSerializer(serializers.ModelSerializer):
    """Создание чата между пользователями"""

    participants = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )

    chat_name = serializers.CharField(
        required=False,
        allow_blank=True
    )

    class Meta:
        model = Chat
        fields = [
            'id',
            'participants',
            'chat_name',
            'is_group'
        ]

    def validate_participants(self, phone_numbers):
        """Проверка: все ли номера существуют в базе"""
        unique_numbers = list(set(phone_numbers))
        users = CustomUser.objects.filter(phone_number__in=unique_numbers)

        if users.count() != len(unique_numbers):
            raise serializers.ValidationError("Некоторые номера не найдены")

        return unique_numbers

    def validate_chat_name(self, value):
        """Проверка на уникальность названия для групповых чатов"""
        is_group = self.initial_data.get('is_group')
        is_group = str(is_group).lower() in ['true', '1', 'yes']

        if is_group and value:
            if Chat.objects.filter(chat_name=value).exists():
                raise serializers.ValidationError("Чат с таким названием уже существует.")
        return value

    def create(self, validated_data):
        request_user = self.context['request'].user

        if not request_user.is_authenticated:
            raise serializers.ValidationError("Пользователь не авторизован.")

        phone_numbers = validated_data.get('participants', [])
        if not phone_numbers:
            raise serializers.ValidationError("Невозможно создать чат без участников.")

        users = list(CustomUser.objects.filter(phone_number__in=phone_numbers))

        # Добавляем себя в чат, если не включили
        if request_user not in users:
            users.append(request_user)

        if not users:
            raise serializers.ValidationError("Невозможно создать чат без участников.")

        is_group = len(users) > 2
        chat_name = validated_data.get('chat_name')  # TODO: прочитай чем отличается get метод для словаря и чем отличается от квадратных скобок!

        if is_group is True and chat_name is None:
            # если создается группа и если фронтенд не передал название чата
            raise serializers.ValidationError(
                {'chat_name': "При создании чата из больше чем два пользователя нужно ввести название чата"},
            )

        # Повторная проверка на уникальность имени группового чата
        # TODO: могут существовать разные чаты с одинаковым названием, поэтому это валидация нам не нужна
        # if is_group and chat_name:
        #     if Chat.objects.filter(chat_name=chat_name).exists():
        #         raise serializers.ValidationError({'chat_name': 'Чат с таким названием уже существует.'})

        # Проверка на существующий личный чат
        if not is_group:
            user_ids = set(user.id for user in users)
            for chat in Chat.objects.filter(is_group=False):
                participant_ids = set(chat.participants.values_list('id', flat=True))
                if participant_ids == user_ids:
                    return chat

        chat = Chat.objects.create(
            is_group=is_group,
            chat_name=chat_name,
        )
        chat.participants.set(users)
        return chat


class ChatUpdateSerializer(serializers.ModelSerializer):
    """Обновление названия чата"""
    class Meta:
        model = Chat
        fields = ['chat_name']
