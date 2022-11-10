import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.utils import POST_ON_PAGE

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.user_hnn = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test_slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author = Client()
        self.author.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_hnn)
        self.guest_client = Client()

    def test_page_accessible_by_name(self):
        """URL, генерируемые при помощи имен, доступны."""
        destination_urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:post_detail',
                    kwargs={'post_id': ViewsTests.post.id}),
            reverse('posts:post_edit', kwargs={'post_id': ViewsTests.post.id}),
            reverse('posts:follow_index'),
        ]
        for destination_url in destination_urls:
            with self.subTest(destination_url=destination_url):
                response = self.author.get(destination_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_use_correct_templates(self):
        """При запросе к URLS соответсвует шаблону"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': ViewsTests.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': ViewsTests.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_view_context_pages(self):
        """Проверка контекста."""
        post = Post.objects.all()
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        )
        tested_fields = {
            'text',
            'group',
            'author',
            'image',
        }
        for reverse_name in pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                for field in tested_fields:
                    self.assertEqual(
                        getattr((response.context['page_obj'][0]), field),
                        getattr(post.get(
                            id=response.context['page_obj'][0].id), field)
                    )

    def test_view_post_detail_context(self):
        """Проверка контекста на странице post_detail"""
        post = Post.objects.get(id=ViewsTests.post.id)
        Tested_context_values = {
            'post': post,
            'post_num': post.author.posts.count(),
        }
        for context_param, context_value in Tested_context_values.items():
            with self.subTest(context_param=context_param):
                response = self.author.get(
                    reverse('posts:post_detail',
                            kwargs={'post_id': ViewsTests.post.id}))
                self.assertEqual(
                    response.context.get(context_param), context_value)

    def test_view_create_and_edit_context(self):
        """Проверка контекста на страницах создания и редактирования поста."""
        pages = {
            reverse('posts:post_create'): False,
            reverse('posts:post_edit',
                    kwargs={'post_id': ViewsTests.post.id}): True,
        }
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField
        }
        for page, is_edit_value in pages.items():
            response = self.author.get(page)
            with self.subTest(is_edit_value=is_edit_value):
                self.assertEqual(response.context.get('is_edit'),
                                 is_edit_value)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_create_post_in_pages(self):
        """Дополнительная проверка при создании поста."""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        for page in pages:
            response = self.author.get(page)
            post = response.context['page_obj'][0]
            post_field = {
                f'{post.text}': ViewsTests.post.text,
                f'{post.author.username}': ViewsTests.post.author.username,
                f'{post.group.id}': f'{ViewsTests.group.id}',
            }
            for page_value, reference_value in post_field.items():
                with self.subTest(page_value=page_value):
                    self.assertEqual(page_value, reference_value)

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы"""
        post_new = Post.objects.create(
            author=self.user,
            text='Текст для проверки кеширования главной страницы',
            group=self.group,
        )
        post_del = Post.objects.get(id=post_new.id)
        response = self.author.get(reverse('posts:index'))
        post_del.delete()
        response_cached = self.author.get(reverse('posts:index'))
        self.assertEqual(response.content, response_cached.content)
        cache.clear()
        response_cached = self.author.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_cached.content)

    def test_follow_for_guest(self):
        """Проверка подписки для гостя"""
        follow_count = Follow.objects.count()
        response = self.guest_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}),
            follow=True
        )
        self.assertRedirects(response, reverse('users:login')
                             + f'?next=/profile/{self.user.username}/follow/')
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_for_auth_user(self):
        """Проверка подписки для авторизованного пользователя"""
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}),
            follow=True)
        self.assertRedirects(response, reverse('posts:follow_index'))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        response = self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user.username}),
            follow=True)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user.username}))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_for_new_post(self):
        """Проверка изменения подписки"""
        response = self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}),
            follow=True)
        posts_count = len(response.context['page_obj'])
        new_post = Post.objects.create(
            author=self.user,
            text='Новый пост для подписчиков теста.',)
        post = Post.objects.get(id=new_post.id)
        response = self.authorized_client.post(
            reverse('posts:follow_index'))
        posts_count_2 = len(response.context['page_obj'])
        self.assertEqual(posts_count + 1, posts_count_2)
        post.delete()
        response = self.authorized_client.post(
            reverse('posts:follow_index'))
        posts_count_2 = len(response.context['page_obj'])
        self.assertEqual(posts_count, posts_count_2)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug'
        )
        for i in range(POST_ON_PAGE + 2):
            Post.objects.create(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.author = Client()
        self.author_post = PaginatorViewsTests.user
        self.author.force_login(self.author_post)

    def test_first_page_contains_records(self):
        """Тестирование паджинатора, страница 1."""
        response_list = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for reverse_name in response_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertEqual(
                    len(response.context.get('page_obj')), POST_ON_PAGE)

    def test_second_page_contains_two_records(self):
        """Тестирование паджинатора, страница 2."""
        response_list = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for reverse_name in response_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context.get('page_obj')), 2)
