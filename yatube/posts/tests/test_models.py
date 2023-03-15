from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        cls.post_field_verboses = [
            ('text', 'Ваш пост'),
            ('pub_date', 'Дата публикации'),
            ('author', 'Автор публикации'),
            ('group', 'Группа'),
            ('image', 'Картинка'),
        ]

        cls.group_field_verboses = [
            ('title', 'Название'),
            ('slug', 'Краткая ссылка'),
            ('description', 'Описание'),
        ]

        cls.post_field_help_texts = [
            ('text', 'Место для вашей публикации'),
            ('pub_date', 'Здесь будет отражена дата вашего поста'),
            ('author', 'Введите имя автора'),
            ('group', ('Выберите группу, к которой вы '
                       'хотели бы отнести ваш пост (по желанию)')),
            ('image', 'Картинка, которая будет прикреплена к посту'),
        ]

        cls.group_field_help_texts = [
            ('title', 'Укажите название группы'),
            ('slug', 'Укажите адрес страницы'),
            ('description', 'Введите описание группы'),
        ]

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        str_correct = [
            (str(self.group), self.group.title),
            (str(self.post), self.post.text[:Post.POST_TEXT_TO_PRINT]),
        ]
        for object_name, expected_object_name in str_correct:
            with self.subTest(object_name=object_name):
                self.assertEqual(
                    object_name, expected_object_name
                )

    def test_verbose_name_post(self):
        """verbose_name в полях поста совпадает с ожидаемым."""
        for field, expected_value in self.post_field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_verbose_name_group(self):
        """verbose_name в полях группы совпадает с ожидаемым."""
        for field, expected_value in self.group_field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_post(self):
        """help_text в полях поста совпадает с ожидаемым."""
        for field, expected_value in self.post_field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value
                )

    def test_help_text_group(self):
        """help_text в полях группы совпадает с ожидаемым."""
        for field, expected_value in self.group_field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).help_text, expected_value
                )
