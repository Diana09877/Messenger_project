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
        unique=True,
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
    likes = models.ManyToManyField(
        CustomUser,
        related_name='liked_messages'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Автор'
    )
    content = models.TextField(
        verbose_name='Текст сообщения',
        validators=[MinLengthValidator(
            1,
            "Сообщение не может быть пустым")]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата отправки'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
        ]
