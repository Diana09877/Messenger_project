from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from .models import CustomUser
from rest_framework.authtoken.models import Token

class UserTests(APITestCase):

    def setUp(self):
        self.user_data = {
            'phone_number': '0555980082',
            'password': 'password_123',
            'first_name': '',
            'last_name': ''

        }

        self.user = CustomUser.objects.create_user(
            phone_number=self.user_data['phone_number'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            password=self.user_data['password']
        )
        self.token = Token.objects.create(user=self.user)
        self.auth_header = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    def test_registration(self):
        url = reverse('register')
        data = {
            'phone_number': '1234567',
            'first_name': '',
            'last_name': '',
            'password': 'qwerty0987654',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_login(self):
        url = reverse('login')
        data = {
            'phone_number': self.user_data['phone_number'],
            'password': self.user_data['password'],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_get_profile_authenticated(self):
        url = reverse('user-profile')
        response = self.client.get(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.user_data['phone_number'])

    def test_update_profile_partial(self):
        url = reverse('user-profile')
        data = {'first_name': ''}
        response = self.client.patch(url, data, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], '')

    def test_user_search(self):
        CustomUser.objects.create_user(
            phone_number='777555000',
            first_name='Иван',
            last_name='',
            password='asdfg5555'
        )
        url = reverse('user-search') + '?search=Ива'
        response = self.client.get(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any('Иван' in user['first_name'] for user in response.data))
