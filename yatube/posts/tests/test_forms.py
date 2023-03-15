import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ..models import Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
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
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user_author)

    def test_create_post_form(self):
        """Валидная форма создает пост в Yatube с картинкой."""
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='new_img-test.jpg',
            content=self.pic,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост 1',
            'group': self.post.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username})
        )
        self.assertEqual(Post.objects.count(), 1)
        created_post = Post.objects.first()
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.group.pk, form_data['group'])
        self.assertEqual(created_post.image, f'posts/{uploaded}')

    def test_edit_post_form(self):
        """Валидная форма со страницы редактирования поста
        изменяет пост.
        """
        uploaded = SimpleUploadedFile(
            name='new_img-test-2.jpg',
            content=self.pic,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост после редактирования',
            'group': self.post.group.pk,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.select_related(
            'author', 'group').get(pk=self.post.pk)
        self.assertEqual(edited_post.author.username,
                         self.user_author.username)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.pk, form_data['group'])
        self.assertEqual(edited_post.image, f'posts/{uploaded}')
