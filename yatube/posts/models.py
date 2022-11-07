from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Название',
                             help_text='Введите название')
    slug = models.SlugField(max_length=255,
                            unique=True,
                            db_index=True,
                            verbose_name='URL')
    description = models.TextField(verbose_name='Описание',
                                   help_text='Введите описание группы')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста',
                            help_text='Введите текст поста')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор')
    group_help_text = 'Группа, к которой будет относиться пост'
    group = models.ForeignKey('Group',
                              verbose_name='Группа',
                              help_text=group_help_text,
                              on_delete=models.SET_NULL,
                              related_name='groups',
                              blank=True,
                              null=True)
    image = models.ImageField(verbose_name='Картинка',
                              help_text='Изображение',
                              upload_to='posts/',
                              blank=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Пост',)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор')
    text = models.TextField(verbose_name='Текст комментария',
                            help_text='Введите текст комментанрия')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Интересный автор')
