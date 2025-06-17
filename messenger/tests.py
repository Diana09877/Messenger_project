from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from messenger.models import Chat, Message

CustomUser = get_user_model()


class ChatAPITests(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            phone_number='0555980082', password='password_123', first_name=''
        )
        self.user2 = CustomUser.objects.create_user(
            phone_number='1234567', password='qwerty0987654', first_name=''
        )
        self.user3 = CustomUser.objects.create_user(
            phone_number='777555000', password='asdfg5555', first_name=''
        )

        self.private_chat = Chat.objects.create(is_group=False)
        self.private_chat.participants.add(self.user1, self.user2)

        self.group_chat = Chat.objects.create(is_group=True, chat_name='Test Group')
        self.group_chat.participants.add(self.user1, self.user2)

        self.message1 = Message.objects.create(
            chat=self.private_chat, author=self.user1, content='Hello private'
        )
        self.message2 = Message.objects.create(
            chat=self.group_chat, author=self.user2, content='Hello group'
        )

    def authenticate_user(self, user):
        self.client.force_authenticate(user=user)

    def test_create_private_chat(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-create')
        data = {'is_group': False, 'participants': [self.user3.id]}
        response = self.client.post(url, data, format='json')
        print('DEBUG RESPONSE DATA:', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_group_chat(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-create')
        data = {
            'is_group': True,
            'chat_name': 'New Group',
            'participants': [self.user1.id, self.user2.id, self.user3.id],
        }
        response = self.client.post(url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chat.objects.count(), 3)
        self.assertEqual(len(response.data['participants']), 3)

    def test_chat_list_authenticated(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_chat_list_unauthenticated(self):
        url = reverse('chat-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_private_chat_detail_as_participant(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-detail', kwargs={'chat_id': self.private_chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.private_chat.id)
        self.assertEqual(len(response.data['messages']), 1)

    def test_private_chat_detail_as_non_participant(self):
        self.authenticate_user(self.user3)
        url = reverse('chat-detail', kwargs={'chat_id': self.private_chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_group_chat_detail_as_participant(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-detail', kwargs={'chat_id': self.group_chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['messages']), 1)

    def test_group_chat_detail_as_non_participant(self):
        self.authenticate_user(self.user3)
        url = reverse('chat-detail', kwargs={'chat_id': self.group_chat.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chat_name'], 'Test Group')
        self.assertEqual(response.data['messages'], [])

    def test_update_group_chat_name(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-update', kwargs={'pk': self.group_chat.id})
        data = {'chat_name': 'Updated Group Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group_chat.refresh_from_db()
        self.assertEqual(self.group_chat.chat_name, 'Updated Group Name')

    def test_update_private_chat_name(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-update', kwargs={'pk': self.private_chat.id})
        data = {'chat_name': 'Should Fail'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_chat_by_non_participant(self):
        self.authenticate_user(self.user3)
        url = reverse('chat-update', kwargs={'pk': self.group_chat.id})
        data = {'chat_name': 'Hacked Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_join_group_chat(self):
        self.authenticate_user(self.user3)
        url = reverse('chat-join', kwargs={'chat_id': self.group_chat.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.group_chat.participants.filter(id=self.user3.id).exists())

    def test_join_already_joined(self):
        self.authenticate_user(self.user1)
        url = reverse('chat-join', kwargs={'chat_id': self.group_chat.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Вы уже участник чата.')

    def test_send_message_without_access(self):
        self.authenticate_user(self.user3)
        url = reverse('message-send')
        data = {'chat': self.private_chat.id, 'content': 'Should fail'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_like_message_as_participant(self):
        self.authenticate_user(self.user1)
        url = reverse('message-like', kwargs={'message_id': self.message2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.message2.likes.filter(id=self.user1.id).exists())

    def test_like_message_as_non_participant(self):
        self.authenticate_user(self.user3)
        url = reverse('message-like', kwargs={'message_id': self.message2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_like(self):
        self.authenticate_user(self.user1)
        url = reverse('message-like', kwargs={'message_id': self.message1.id})

        # Лайк
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.message1.likes.filter(id=self.user1.id).exists())

        # Анлайк
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.message1.likes.filter(id=self.user1.id).exists())
