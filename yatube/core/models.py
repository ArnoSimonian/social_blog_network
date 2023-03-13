from django.db import models


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Дата создания",
        help_text="Здесь будет отражена дата вашей записи",
    )

    class Meta:
        abstract = True
