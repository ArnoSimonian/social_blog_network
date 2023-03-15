from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name="Название",
        help_text="Укажите название группы",
        max_length=200
    )
    slug = models.SlugField(
        verbose_name="Краткая ссылка",
        help_text="Укажите адрес страницы",
        unique=True
    )
    description = models.TextField(
        verbose_name="Описание",
        help_text="Введите описание группы"
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    POST_TEXT_TO_PRINT: int = 15
    text = models.TextField(
        verbose_name="Ваш пост",
        help_text="Место для вашей публикации"
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        help_text="Здесь будет отражена дата вашего поста",
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Автор публикации",
        help_text="Введите имя автора"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name="Группа",
        help_text="Выберите группу, к которой вы "
                  "хотели бы отнести ваш пост (по желанию)"
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name="Картинка",
        help_text="Картинка, которая будет прикреплена к посту"
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self) -> str:
        return self.text[:Post.POST_TEXT_TO_PRINT]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Cсылка на пост",
        help_text="Добавляет ссылку на пост, к которому будет"
                  "оставлен комментарий"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Ссылка на автора комментария",
        help_text="Добавляет ссылку на автора комментария"
    )
    text = models.TextField(
        verbose_name="Ваш комментарий",
        help_text="Место для вашего комментария"
    )
    created = models.DateTimeField(
        verbose_name="Дата комментария",
        help_text="Здесь будет отражена дата вашего комментария",
        auto_now_add=True
    )

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
        help_text="Пользователь, имеющий подписки на авторов"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор постов",
        help_text="Автор постов с подписками"
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(check=~models.Q(author=models.F('user')),
                                   name='could_not_follow_itself'),
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_following'),
        ]
