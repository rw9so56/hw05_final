from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import page_paginator


def index(request):
    """Главная страница"""
    template = 'posts/index.html'
    post_list = Post.objects.all()
    context = {
        'page_obj': page_paginator(request, post_list),
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Cтраница сообщества"""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
        'page_obj': page_paginator(request, group.groups.all()),
    }
    return render(request, template, context)


def profile(request, username):
    """Страница с информацией об авторе"""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    following = ((request.user.id is not None)
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists())
    context = {
        'author': author,
        'page_obj': page_paginator(request, author.posts.all()),
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница с информацией поста"""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    post_num = post.author.posts.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'post_num': post_num,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Переход на страницу создания поста"""
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:profile', request.user)
    form = PostForm()
    context = {
        'is_edit': False,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Переход на страницу редактирования поста"""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'is_edit': True,
        'post': post,
        'form': form,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту на странице детальных записей"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница постов интересных авторов(мои подписки)"""
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    context = {'page_obj': page_paginator(request, posts)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    user = request.user
    follow = Follow.objects.filter(user=user, author=author)
    if user != author and not follow.exists():
        follow = Follow.objects.create(user=user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора"""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username=username)
