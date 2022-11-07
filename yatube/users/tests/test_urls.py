from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_hnn = User.objects.create_user(username='HasNoName')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_hnn)

    def test_users_url_exists_authorized_user(self):
        """Проверка доступности адресов uers."""
        pages = [
            '/auth/logout/',
            '/auth/signup/',
            # '/auth/password_change/',
            # '/auth/password_change/done/',
            '/auth/password_reset/',
            '/auth/password_reset_confirm/',
            '/auth/password_reset/done/',
            # reset/<uidb64>/<token>/
            '/auth/reset/done/'
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)
