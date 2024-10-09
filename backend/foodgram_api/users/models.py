from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.constants import AVATAR_DIR


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to=AVATAR_DIR, 
        null=True,  
        default=None,
        blank=True,
        verbose_name = 'Аватар'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
 
    def is_subscribed(self):
        return True
    
    def __str__(self):
        return self.username
