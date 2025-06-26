from django.db import models
from django.core.validators import MinLengthValidator
from users.models import CustomUser


class Chat(models.Model):
    """Модель чата между пользователями"""
    participants = models.ManyToManyField(
        CustomUser,
        related_name='chats',
        verbose_name='Участники',
        help_text='Пользователи, участвующие в чате'
    )
    chat_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Название чата'
    )
    is_group = models.BooleanField(
        default=False,
        verbose_name='Группа'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата последнего обновления'
    )
    deleted_for = models.ManyToManyField(
        CustomUser, related_name='hidden_chats', blank=True,
        verbose_name='Скрыто для'
    )

    def is_visible_to(self, user):
        """Проверка, видит ли пользователь этот чат"""
        return user not in self.deleted_for.all()

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]


class Message(models.Model):
    """Модель сообщения в чате"""
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат',
        help_text='Чат, к которому относится сообщение'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Автор'
    )
    content = models.TextField(
        verbose_name='Текст сообщения',
        validators=[MinLengthValidator(1, "Сообщение не может быть пустым")]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата отправки'
    )
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    deleted_for = models.ManyToManyField(
        CustomUser, related_name='hidden_messages', blank=True,
        verbose_name='Скрыто для'
    )

    def is_visible_to(self, user):
        """Проверяет, видно ли сообщение пользователю (не удалено и не скрыто)"""
        return user not in self.deleted_for.all() and not self.is_deleted

    def like_count(self):
        """Возвращает количество лайков для сообщения"""
        return self.likes.count()

    def liked_by_user(self, user):
        """Проверяет, лайкал ли пользователь это сообщение"""
        return self.likes.filter(user=user).exists()

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
        ]


class MessageLike(models.Model):
    """Связь лайков между пользователями и сообщениями"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='message_likes',
        verbose_name='Пользователь'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Сообщение'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата лайка')

    class Meta:
        unique_together = ('user', 'message')
        verbose_name = 'Лайк сообщения'
        verbose_name_plural = 'Лайки сообщений'

    def __str__(self):
        return f"{self.user.phone_number} liked message {self.message.id}"

