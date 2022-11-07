from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User

import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug='test_slug'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        self.author = Client()
        self.author.force_login(self.user)

    def test_create_post_from_guest(self):
        """Тест гость не может создать пост Post."""
        count_posts = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Текст создаваемого поста',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertRedirects(response, reverse('users:login')
                             + '?next=/create/')

    def test_create_post_from_author(self):
        """Тест авторизированный пользователь создает пост Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Текст создаваемого поста',
            'image': uploaded,
        }
        response = self.author.post(reverse('posts:post_create'),
                                    data=form_data,
                                    follow=True,)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': 'auth'}))
        self.assertTrue(Post.objects.filter(
                        author=self.user.id,
                        group=self.group.id,
                        text='Текст создаваемого поста',
                        ).exists())

    def test_edit_from_guest(self):
        """Тест гость не может редактировать пост Post"""
        post_id = PostCreateFormTests.post.id
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Текст редактируемого поста',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{post_id}/edit/'
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_from_author(self):
        """Автор поста может редактировать пост Post."""
        post_id = PostCreateFormTests.post.id
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Текст редактируемого поста',
        }
        response = self.author.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': post_id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])

    def test_form_edit_post(self):
        """Форма редактирует запись поста в Post."""
        post_id = PostCreateFormTests.post.id
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Текст редактируемого поста',
        }
        response = self.author.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': post_id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])
