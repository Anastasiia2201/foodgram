from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from recipes.constants import (AVATAR_DIR, CHAR_FIELD_MAX_LENGTH,
                               MAX_LENGTH_EMAIL)


class Roles(models.TextChoices):
    USER = "user", _("Пользователь")
    ADMIN = "admin", _("Администратор")


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password"]
    avatar = models.ImageField(
        upload_to=AVATAR_DIR,
        verbose_name="Аватар",
        null=True,
        blank=True,
    )
    role = models.CharField(
        verbose_name="Роль",
        max_length=CHAR_FIELD_MAX_LENGTH,
        choices=Roles.choices,
        default=Roles.USER,
    )
    email = models.EmailField(
        unique=True,
        max_length=MAX_LENGTH_EMAIL,
        verbose_name="Почта",
    )

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "Пользователи"
        ordering = ("id",)

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == Roles.ADMIN or self.is_superuser
