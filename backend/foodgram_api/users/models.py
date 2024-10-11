from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.constants import AVATAR_DIR


class Roles:
    USER = 'user'
    ADMIN = 'admin'
    CHOICES = (
        (USER, 'Пользователь'),
        (ADMIN, 'Администратор'),
    )

    @classmethod
    def max_length_number_role(cls):
        return max(len(role) for role, _ in cls.CHOICES)


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to=AVATAR_DIR, 
        null=True,  
        default=None,
        blank=True,
        verbose_name = 'Аватар'
    )
    role = models.CharField(
        'Роль',
        max_length=Roles.max_length_number_role(),
        choices=Roles.CHOICES,
        default=Roles.USER
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username
 
    def is_subscribed(self):
        return True

    @property
    def is_admin(self):
        return self.role == Roles.ADMIN or self.is_superuser
