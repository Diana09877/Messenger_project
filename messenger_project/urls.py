from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from users.views import (
    UserRegistrationAPIView, UserLoginAPIView, UserSearchAPIView,
    UserProfileAPIView
)
from messenger.views import (
    MessageCreateAPIView, MessageLikeAPIView, ChatJoinAPIView, ChatSearchAPIView, ChatListCreateAPIView,
    ChatRetrieveUpdateAPIView
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Messenger API",
      default_version='v1',
      description="Документация для API чата",
   ),
   public=True,
   permission_classes=[permissions.AllowAny,],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('swagger/docs/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Аутентификация и профиль
    path('api/v1/login/', UserLoginAPIView.as_view(), name='login'),
    path('api/v1/register/', UserRegistrationAPIView.as_view(), name='register'),
    path('api/v1/profile/', UserProfileAPIView.as_view(), name='user-profile'),

    # Пользователи
    path('api/v1/users/search/', UserSearchAPIView.as_view(), name='user-search'),

    # Чаты
    path('api/v1/chats/', ChatListCreateAPIView.as_view(), name='chat-list-create'),  # GET и POST
    path('api/v1/chats/<int:pk>/', ChatRetrieveUpdateAPIView.as_view(), name='chat-detail-update'),  # GET, PUT/PATCH
    path('api/v1/chats/<int:chat_id>/join/', ChatJoinAPIView.as_view(), name='chat-join'),
    path('api/v1/chats/search/', ChatSearchAPIView.as_view(), name='chat-search'),

    # Сообщения
    path('api/v1/messages/', MessageCreateAPIView.as_view(), name='message-send'),  # POST
    path('api/v1/messages/<int:message_id>/like/', MessageLikeAPIView.as_view(), name='message-like'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)