from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def paginate(page_number, post_list, posts_on_the_page_num):
    paginator = Paginator(post_list, posts_on_the_page_num)
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group')
    posts_on_the_page_num = settings.POSTS_ON_THE_PAGE_NUM
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginate(page_number, post_list, posts_on_the_page_num),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    posts_on_the_page_num = settings.POSTS_ON_THE_PAGE_NUM
    page_number = request.GET.get('page')
    context = {
        'group': group,
        'page_obj': paginate(page_number, post_list, posts_on_the_page_num),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )
    posts_on_the_page_num = settings.POSTS_ON_THE_PAGE_NUM
    page_number = request.GET.get('page')
    context = {
        'author': author,
        'following': following,
        'page_obj': paginate(page_number, post_list, posts_on_the_page_num),
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related('author', 'group'),
                             pk=post_id)
    comments = post.comments.select_related('author', 'post')
    form = CommentForm(
        request.POST or None
    )
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post.objects.select_related('author', 'group'),
                             pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author', 'group'),
                             pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.select_related('author', 'group').filter(
        author__following__user=request.user)
    posts_on_the_page_num = settings.POSTS_ON_THE_PAGE_NUM
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginate(page_number, post_list, posts_on_the_page_num),
        'follow': True,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    follower = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    )
    follower.delete()
    return redirect('posts:profile', username)
