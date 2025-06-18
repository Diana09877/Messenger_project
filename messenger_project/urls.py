from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from users.views import (
    UserRegistrationAPIView, UserLoginAPIView, UserSearchAPIView,
    UserProfileAPIView
)
from messenger.views import (
    MessageCreateAPIView, MessageLikeAPIView, ChatDetailAPIView,ChatListAPIView,
    ChatCreateAPIView, ChatUpdateAPIView, ChatJoinAPIView, ChatSearchAPIView
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Chat API",
      default_version='v1',
      description="Документация для API чата",
   ),
   public=True,
   permission_classes=[permissions.AllowAny,],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/register/', UserRegistrationAPIView.as_view(), name='register'),
    path('api/v1/login/', UserLoginAPIView.as_view(),name='login'),
    path('api/v1/profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('api/v1/chat/create/', ChatCreateAPIView.as_view(), name='chat-create'),
    path('api/v1/chat/<int:pk>/update/', ChatUpdateAPIView.as_view(), name='chat-update'),
    path('api/v1/user-search/', UserSearchAPIView.as_view(), name='user-search'),
    path('api/v1/chat/<int:chat_id>/', ChatDetailAPIView.as_view(), name='chat-detail'),
    path('api/v1/chats/', ChatListAPIView.as_view(), name='chat-list'),
    path('chats/<int:chat_id>/join/', ChatJoinAPIView.as_view(), name='chat-join'),
    path('api/v1/messages/send/', MessageCreateAPIView.as_view(), name='message-send'),
    path('api/v1/messages/<int:message_id>/like/', MessageLikeAPIView.as_view(), name='message-like'),
    path('api/v1/chat-search/', ChatSearchAPIView.as_view(), name='chat-search'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)