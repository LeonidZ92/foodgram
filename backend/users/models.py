from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from foodgram import constants


class User(AbstractUser):
    """Модель для пользователей"""

    username = models.CharField(
        max_length=constants.USERNAME_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='Имя пользователя содержит запрещенные символы.'
                    'Используйте только буквы, цифры и символы .@+-',
        ), ],
        verbose_name='Уникальное имя пользователя',
    )
    email = models.EmailField(
        max_length=constants.EMAIL_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Адрес электронной почты',
    )
    first_name = models.CharField(
        max_length=constants.FIRST_NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        max_length=constants.LAST_NAME_MAX_LENGTH,
    )
    password = models.CharField(
        max_length=constants.PASSWORD_MAX_LENGTH,
    )
    avatar = models.ImageField(
        blank=True,
        null=True,
        upload_to='media/avatars/',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для подписок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='check_follower_author',
            ),
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
