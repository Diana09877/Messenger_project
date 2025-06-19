from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from messenger.models import CustomUser


class UserProfileAPITest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone_number='+123456789',
            password='password123',
            first_name='Timur',
            last_name='Avazbekov'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user-profile')

    def test_get_user_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '+123456789')
        self.assertEqual(response.data['first_name'], 'Timur')

    def test_update_user_profile_put(self):
        data = {
            'first_name': 'Artur',
            'last_name': 'Arturov',
        }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Artur')
        self.assertEqual(self.user.last_name, 'Arturov')

    def test_partial_update_user_profile_patch(self):
        data = {
            'first_name': 'Adilet'
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Adilet')


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.phone_number = '+1234567890'
        self.password = 'securepassword123'
        self.first_name = 'Artur'

    def test_user_registration(self):
        data = {
            'phone_number': self.phone_number,
            'password': self.password,
            'first_name': self.first_name

        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(phone_number=self.phone_number).exists())

    def test_user_login(self):
        CustomUser.objects.create_user(phone_number=self.phone_number, password=self.password)

        data = {
            'phone_number': self.phone_number,
            'password': self.password,
            'first_name': self.first_name,
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class UserSearchAPITest(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            phone_number='+12345678',
            password='testpassword',
            first_name='Maksat'
        )
        self.user2 = CustomUser.objects.create_user(
            phone_number='+87654321',
            password='testpassword',
            first_name='Asema'
        )
        self.user3 = CustomUser.objects.create_user(
            phone_number='+11112222',
            password='testpassword',
            first_name='Adilet'
        )

        self.client.force_authenticate(user=self.user1)

    def test_search_by_phone_number(self):
        url = reverse('user-search')
        response = self.client.get(url, {'search': '+8765'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['phone_number'], '+87654321')

    def test_search_by_first_name(self):
        url = reverse('user-search')
        response = self.client.get(url, {'search': 'Adi'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'Adilet')

    def test_search_excludes_current_user(self):
        url = reverse('user-search')
        response = self.client.get(url, {'search': '+123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


