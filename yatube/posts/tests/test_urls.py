from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='TestAuthUser')
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_author,
            group=cls.group,
        )

        cls.reverse_names_expected_url_names = [
            ('posts:index', '/', {}),
            ('posts:group_list', f'/group/{cls.post.group.slug}/',
                                 {'slug': cls.post.group.slug}),
            ('posts:profile', f'/profile/{cls.post.author.username}/',
                              {'username': cls.post.author.username}),
            ('posts:post_detail', f'/posts/{cls.post.pk}/',
                                  {'post_id': cls.post.pk}),
            ('posts:post_create', '/create/', {}),
            ('posts:post_edit', f'/posts/{cls.post.pk}/edit/',
                                {'post_id': cls.post.pk}),
            ('posts:add_comment', f'/posts/{cls.post.pk}/comment/',
                                  {'post_id': cls.post.pk}),
            ('posts:follow_index', '/follow/', {}),
            ('posts:profile_follow',
             f'/profile/{cls.post.author.username}/follow/',
             {'username': cls.post.author.username}),
            ('posts:profile_unfollow',
             f'/profile/{cls.post.author.username}/unfollow/',
             {'username': cls.post.author.username}),
            ('users:login', '/auth/login/', {}),
        ]

        cls.reverse_names_status_code = [
            (reverse('posts:index'), HTTPStatus.OK, False),
            (reverse('posts:group_list', kwargs={'slug': cls.post.group.slug}),
             HTTPStatus.OK, False),
            (reverse('posts:profile',
             kwargs={'username': cls.post.author.username}),
             HTTPStatus.OK, False),
            (reverse('posts:post_detail', kwargs={'post_id': cls.post.pk}),
             HTTPStatus.OK, False),
            (reverse('posts:post_create'), HTTPStatus.OK, True),
            (reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
             HTTPStatus.OK, True),
            (reverse('posts:follow_index'), HTTPStatus.OK, True),
            ('/unexisting_page/', HTTPStatus.NOT_FOUND, False),
        ]

        cls.login_url = reverse('users:login')
        cls.next_create_url = reverse('posts:post_create')
        cls.next_edit_url = reverse('posts:post_edit', kwargs={'post_id':
                                                               cls.post.pk})
        cls.next_comment_url = reverse('posts:add_comment',
                                       kwargs={'post_id': cls.post.pk})
        cls.next_follow_index_url = reverse('posts:follow_index')
        cls.next_follow_url = reverse('posts:profile_follow',
                                      kwargs={'username':
                                              cls.post.author.username})
        cls.next_unfollow_url = reverse('posts:profile_unfollow',
                                        kwargs={'username':
                                                cls.post.author.username})

        cls.url_names_redirect = [
            (reverse('posts:post_create'),
             f'{cls.login_url}?next={cls.next_create_url}', False),
            (reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
             f'{cls.login_url}?next={cls.next_edit_url}', False),
            (reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
             f'/posts/{cls.post.pk}/', True),
            (reverse('posts:add_comment', kwargs={'post_id': cls.post.pk}),
             f'{cls.login_url}?next={cls.next_comment_url}', False),
            (reverse('posts:add_comment', kwargs={'post_id': cls.post.pk}),
             f'/posts/{cls.post.pk}/', True),
            (reverse('posts:follow_index'),
             f'{cls.login_url}?next={cls.next_follow_index_url}', False),
            (reverse('posts:profile_follow',
                     kwargs={'username': cls.post.author.username}),
             f'{cls.login_url}?next={cls.next_follow_url}', False),
            (reverse('posts:profile_follow',
                     kwargs={'username': cls.post.author.username}),
             f'/profile/{cls.post.author.username}/', True),
            (reverse('posts:profile_unfollow',
                     kwargs={'username': cls.post.author.username}),
             f'{cls.login_url}?next={cls.next_unfollow_url}', False),
            (reverse('posts:profile_unfollow',
                     kwargs={'username': cls.post.author.username}),
             f'/profile/{cls.post.author.username}/', True),
        ]

        cls.reverse_name_templates = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={'slug': cls.post.group.slug}),
             'posts/group_list.html'),
            (reverse('posts:profile',
             kwargs={'username': cls.post.author.username}),
             'posts/profile.html'),
            (reverse('posts:post_detail', kwargs={'post_id': cls.post.pk}),
             'posts/post_detail.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
             'posts/create_post.html'),
            (reverse('posts:follow_index'), 'posts/follow.html'),
            ('/unexisting_page/', 'core/404.html'),
        ]

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user_auth)

    def test_url_names_are_equal_to_reverse_names(self):
        """Обращение к имени страницы в urlpatterns возвращает
        верный URL-адрес.
        """
        for name, expected, kwargs in self.reverse_names_expected_url_names:
            with self.subTest(name=name, kwargs=kwargs):
                got = reverse(name, kwargs=kwargs)
                self.assertEqual(got, expected)

    def test_urls_exist_at_desired_location(self):
        """Страницы доступны пользователям в зависимости
        от статуса их авторизации.
        """
        self.authorized_client.force_login(PostURLTests.user_author)
        for reverse_name, status_code, auth_is_needed in (
            self.reverse_names_status_code
        ):
            with self.subTest(reverse_name=reverse_name):
                if auth_is_needed:
                    response = self.authorized_client.get(reverse_name)
                else:
                    response = self.guest_client.get(reverse_name)
            self.assertEqual(response.status_code, status_code)

    def test_urls_redirect(self):
        """Страницы перенаправляют пользователей в зависимости
        от статуса их авторизации.
        """
        for reverse_name, redirect_address, client_is_auth in (
            self.url_names_redirect
        ):
            with self.subTest(reverse_name=reverse_name):
                if client_is_auth:
                    response = self.authorized_client.get(reverse_name,
                                                          follow=True)
                else:
                    response = self.guest_client.get(reverse_name, follow=True)
            self.assertRedirects(response, redirect_address)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        self.authorized_client.force_login(PostURLTests.user_author)
        for reverse_name, template in self.reverse_name_templates:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
