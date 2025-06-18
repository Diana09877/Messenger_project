from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from messenger.models import Chat, Message
from users.models import CustomUser


class ChatDetailAPITest(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(phone_number="+12345678", password="pass1234")
        self.user2 = CustomUser.objects.create_user(phone_number="+87654321", password="pass1234")
        self.user3 = CustomUser.objects.create_user(phone_number="+11122222", password="pass1234")

        self.group_chat = Chat.objects.create(chat_name='Group Chat', is_group=True)
        self.group_chat.participants.set([self.user1, self.user2])

        self.private_chat = Chat.objects.create(chat_name='', is_group=False)
        self.private_chat.participants.set([self.user1, self.user3])

        Message.objects.create(chat=self.group_chat, author=self.user1, content="Hi")

        self.url_template = '/api/v1/chat/{}/'

    def test_get_chat_detail_as_participant(self):
        self.client.force_authenticate(user=self.user1)
        url = self.url_template.format(self.group_chat.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chat_name'], 'Group Chat')
        self.assertTrue(response.data['is_group'])
        self.assertIn(self.user1.phone_number, response.data['participants'])
        self.assertGreater(len(response.data['messages']), 0)

    def test_get_group_chat_detail_as_non_participant(self):
        self.client.force_authenticate(user=self.user3)
        url = self.url_template.format(self.group_chat.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chat_id'], self.group_chat.id)
        self.assertEqual(response.data['chat_name'], 'Group Chat')
        self.assertTrue(response.data['is_group'])
        self.assertIn(self.user1.phone_number, response.data['participants'])
        self.assertEqual(response.data['messages'], [])

    def test_get_private_chat_detail_as_non_participant(self):
        self.client.force_authenticate(user=self.user2)
        url = self.url_template.format(self.private_chat.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Доступ запрещён')


class ChatListAPITests(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(phone_number="+123456789", password="testpass")
        self.user2 = CustomUser.objects.create_user(phone_number="+987654321", password="testpass")
        self.chat1 = Chat.objects.create(is_group=False)
        self.chat1.participants.set([self.user1, self.user2])
        self.chat2 = Chat.objects.create(is_group=False)
        self.chat2.participants.set([self.user2])

        self.client.force_authenticate(user=self.user1)

    def test_chat_list_returns_only_user_chats(self):
        url = reverse('chat-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        returned_chat_id = response.data[0]['id']
        self.assertEqual(returned_chat_id, self.chat1.id)


class ChatCreateAPITests(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(phone_number="+12345678", password="testuser")
        self.user2 = CustomUser.objects.create_user(phone_number="+123456789", password="testuser")
        self.user3 = CustomUser.objects.create_user(phone_number="+0987654321", password="testuser")
        self.client.force_authenticate(user=self.user1)

    def test_create_private_chat(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'participants': [self.user2.phone_number],
        }
        response = self.client.post('/api/v1/chat/create/', data)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_group_chat(self):
        self.client.force_authenticate(user=self.user1)

        data = {
            'participants': [
                self.user2.phone_number,
                self.user3.phone_number
            ],
            'chat_name': 'Group Chat'
        }

        response = self.client.post('/api/v1/chat/create/', data)
        print("Group Chat Response:", response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_group'])
        self.assertEqual(response.data['chat_name'], 'Group Chat')


class MessageCreateAPITests(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(phone_number="+12345678", password="testuser")
        self.user2 = CustomUser.objects.create_user(phone_number='0987654321', password='pass1234')

        self.chat = Chat.objects.create(is_group=False)
        self.chat.participants.set([self.user1, self.user2])

        self.url = reverse('message-send')

        self.client.force_authenticate(user=self.user1)

    def test_create_message(self):
        data = {
            'chat_id': self.chat.id,
            'content': 'Привет, это тестовое сообщение!'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['content'], data['content'])

    def test_create_message_no_text(self):
        data = {
            'chat_id': self.chat.id,
            'content': ''
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('content', response.data)


class MessageLikeTest(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(phone_number="+12345678", password="testuser")
        self.user2 = CustomUser.objects.create_user(phone_number="+0987654321", password="testuser")
        self.chat = Chat.objects.create(is_group=False)
        self.chat.participants.set([self.user1, self.user2])
        self.message = Message.objects.create(chat=self.chat, author=self.user1, content='like me')
        self.url = reverse('message-like', kwargs={'message_id': self.message.id})

    def test_like_message(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.message.likes.filter(id=self.user2.id).exists())
        self.assertTrue(response.data['liked'])

    def test_unlike_message(self):
        self.message.likes.add(self.user2)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.message.likes.filter(id=self.user2.id).exists())
        self.assertFalse(response.data['liked'])

    def test_like_message_not_participant(self):
        outsider = CustomUser.objects.create_user(phone_number='5555555555', password='pass1234')
        self.client.force_authenticate(user=outsider)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChatSearchAPITest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(phone_number='+12345678', password='testpass')
        self.client.force_authenticate(user=self.user)

        self.chat1 = Chat.objects.create(chat_name='Football Chat', is_group=True)
        self.chat1.participants.add(self.user)

        self.chat2 = Chat.objects.create(chat_name='Cooking Group', is_group=True)
        self.chat2.participants.add(self.user)

        self.chat3 = Chat.objects.create(chat_name='Music', is_group=True)
        # этот чат без пользователя

    def test_search_chat_by_name(self):
        url = reverse('chat-search')
        response = self.client.get(url, {'q': 'Cook'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['chat_name'], 'Cooking Group')

    def test_search_chat_user_not_included(self):
        url = reverse('chat-search')
        response = self.client.get(url, {'q': 'Music'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
