from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_hnn = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_hnn)
        self.author = Client()
        self.author.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post_id = PostURLTests.post.id
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)

    def test_public_urls(self):
        """Страницы доступны всем пользователям."""
        post_id = PostURLTests.post.id
        pages = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{post_id}/'
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_and_author_post_urls(self):
        """Страницы доступные автору поста и авторизованному пользователю."""
        post_id = PostURLTests.post.id
        page_list = {
            self.author.get(f'/posts/{post_id}/edit/'),
            self.authorized_client.get('/create/'),
            self.authorized_client.get('/follow/'),
        }
        for page in page_list:
            with self.subTest(page=page):
                self.assertEqual(page.status_code, HTTPStatus.OK)

    def test_unexisting_urls(self):
        """Проверка не существующих адресов."""
        pages = [
            '/unexisting_page/',
            '/group/unexisting_slug/',
            '/profile/unexisting_profile/',
            '/posts/99999/'
        ]
        template = 'core/404.html'
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, template)

    def test_redirects_urls(self):
        """Страница createи edit перенаправляет пользователей."""
        post_id = PostURLTests.post.id
        user_destination_pages = {
            self.guest_client.get('/create/', follow=True):
                '/auth/login/?next=/create/',
            self.authorized_client.get(f'/posts/{post_id}/edit/', follow=True):
                f'/posts/{post_id}/',
            self.guest_client.get(f'/posts/{post_id}/edit/', follow=True):
                f'/auth/login/?next=/posts/{post_id}/edit/'
        }
        for response, page in user_destination_pages.items():
            with self.subTest(response=response):
                self.assertRedirects(response, page)
