import math
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.user_follower = User.objects.create_user(
            username='TestUserFollower'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.test_group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug-1',
        )
        cls.pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='img-test.jpg',
            content=cls.pic,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            created=timezone.now(),
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded,
        )
        cls.follow_case = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user_author
        )

        cls.reverse_names_post_list_context = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.post.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': cls.post.author.username}),
            reverse('posts:follow_index'),
        )

        cls.reverse_names_objects = [
            (reverse('posts:group_list', kwargs={'slug': cls.post.group.slug}),
             'group', cls.post.group),
            (reverse('posts:profile',
                     kwargs={'username': cls.post.author.username}),
             'author', cls.post.author),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user_author)

    def check_posts_have_expected_fields(self, post):
        """Все посты формируются с ожидаемыми полями."""
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.created, self.post.created)
        self.assertEqual(post.group.title, self.post.group.title)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.image, self.post.image)

    def test_page_with_post_lists_show_correct_context(self):
        """Шаблоны index, group_list, profile и follow сформированы
        с правильным контекстом.
        """
        self.authorized_client.force_login(PostPagesTests.user_follower)
        for reverse_name in self.reverse_names_post_list_context:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.check_posts_have_expected_fields(
                    response.context['page_obj'][0])

    def test_page_become_correct_objects(self):
        """На страницы группы и профиля автора передаются объекты
        группы и автора соответственно."""
        for reverse_name, context, object in self.reverse_names_objects:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.context.get(context), object)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.check_posts_have_expected_fields(response.context['post'])

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(self.post, form.instance)

    def test_post_with_group_not_on_the_page_with_wrong_group(self):
        """Пост, созданный с указанием группы, не попадает в группу,
        для которой не был предназначен.
        """
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.test_group.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_comment_on_post_detail_page(self):
        """После успешной отправки комментарий появляется на странице поста."""
        comments = {'text': 'Тестовый комментарий'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=comments,
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertContains(response, comments['text'])

    def test_cache_on_index_page_work_correct(self):
        """Проверка кэширования главной страницы."""
        response = self.guest_client.get(reverse('posts:index'))
        page_content = response.content
        Post.objects.first().delete()
        response = self.guest_client.get(reverse('posts:index'))
        cached_page_content = response.content
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        cleared_page_content = response.content
        self.assertEqual(page_content, cached_page_content)
        self.assertNotEqual(cached_page_content, cleared_page_content)


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.user_follower = User.objects.create_user(username='TestFollower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            created=timezone.now(),
            group=cls.group,
            text='Тестовый пост',
        )
        cls.follow_case = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user_author
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowViewsTests.user_follower)

    def test_auth_user_can_follow_other_users(self):
        """Авторизованный пользователь может подписываться
        на других пользователей.
        """
        Follow.objects.all().delete()
        self.authorized_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.post.author.username}))
        self.assertTrue(
            Follow.objects.select_related('author', 'user').filter(
                user=self.user_follower,
                author=self.user_author
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), 1)

    def test_auth_user_can_unfollow_other_users(self):
        """Авторизованный пользователь может удалять
        других пользователей из подписок.
        """
        self.follow_case
        self.authorized_client.post(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.post.author.username}))
        self.assertFalse(
            Follow.objects.select_related('author', 'user').filter(
                user=self.user_follower,
                author=self.user_author
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), 0)

    def test_new_post_is_in_follower_list_and_not_in_not_follower(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан.
        """
        Follow.objects.all().delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_user_cant_follow_itself(self):
        """Подписка на самого себя невозможна."""
        self.authorized_client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.post.author.username}))
        self.assertFalse(
            Follow.objects.select_related('author', 'user').filter(
                user=self.user_author,
                author=self.user_author
            ).exists()
        )


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestUserAuthor')
        cls.user_follower = User.objects.create_user(
            username='TestUserFollower'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            created=timezone.now(),
            group=cls.group,
            text='Тестовый пост',
        )
        cls.follow_case = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user_author
        )
        cls.TEST_POSTS_NUM: int = 27
        cls.PAGE_NUM: int = math.ceil(cls.TEST_POSTS_NUM
                                      / settings.POSTS_ON_THE_PAGE_NUM)
        cls.POSTS_ON_THE_LAST_PAGE: int = (cls.TEST_POSTS_NUM
                                           - settings.POSTS_ON_THE_PAGE_NUM
                                           * (cls.PAGE_NUM - 1)) + 1

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTests.user_follower)
        for post_num in range(self.TEST_POSTS_NUM):
            Post.objects.bulk_create([
                Post(
                    author=self.user_author,
                    created=timezone.now(),
                    group=self.group,
                    text='Тестовый пост' + str(post_num),
                ),
            ])

    def test_paginator(self):
        """Пагинатор корректно разбивает контент на страницы"""
        paginator_pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
            reverse('posts:follow_index'),
        )
        self.follow_case
        for paginator in paginator_pages:
            with self.subTest(paginator=paginator):
                response = self.authorized_client.get(paginator)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_ON_THE_PAGE_NUM)
                response = self.authorized_client.get(
                    paginator + f'?page={self.PAGE_NUM}'
                )
                self.assertEqual(len(response.context['page_obj']),
                                 self.POSTS_ON_THE_LAST_PAGE)
